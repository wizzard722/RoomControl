"""What RoomControl learns per metered device (switches and meters with a power sensor).

Per device (key "<area id>|<part key>", e.g. "keuken|switch:switch.vaatwasser"):
- standby: its power when it is not running (W);
- run_w / peak_w: average and highest power while running;
- cycles: each time it ran (start, minutes, kWh, a 20-point power pattern),
  the last MAX_CYCLES; a run starts above the standby threshold and ends
  after END_IDLE seconds back at standby (pauses in a program count along);
- programs: runs that look alike (duration, kWh and pattern) form one
  program; counted as recognised from PROGRAM_MIN runs. Their names are the
  user's, in the room option "power": {part key: {"programs": {id: name}}};
- heat: how often a run started per weekday and hour;
- days / months / hours: kWh per day (last 60), per month (last 24) and
  per local hour (last 60 days, "YYYY-MM-DDTHH"), for offpay.py;
- kind: guessed from the pattern (guess_kind), the user's choice wins;
- use: per day the quarters of an hour it was in use (last USE_DAYS days),
  for usage.py.

A new device first replays the history Home Assistant still has of its
power sensor (recorder), so it doesn't start from nothing. Kept in
.storage/roomcontrol.devices.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "roomcontrol.devices"
END_IDLE = 600  # s back at standby before a run counts as over
MIN_RUN_MIN = 2.0  # shorter runs are not remembered
MIN_RUN_KWH = 0.005
MAX_CYCLES = 60
PROGRAM_MIN = 3
SIG_POINTS = 20
MAX_GAP = 1800  # s: a longer gap (sensor away) is not counted as energy
DAYS_KEPT = 60
USE_DAYS = 42  # six weeks of use per quarter of an hour
MONTHS_KEPT = 24


def _watts(state: Any) -> float | None:
    if state is None:
        return None
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return None
    unit = str(state.attributes.get("unit_of_measurement") or "W").lower()
    return value * 1000 if unit == "kw" else value


def _sig(samples: list[tuple[float, float]], start: float, end: float) -> list[float]:
    """The run's power pattern: the time-weighted average power in SIG_POINTS equal parts."""
    span = max(end - start, 1.0)
    width = span / SIG_POINTS
    out = []
    for i in range(SIG_POINTS):
        a, b = start + i * width, start + (i + 1) * width
        total = 0.0
        for j, (t, w) in enumerate(samples):
            t_next = samples[j + 1][0] if j + 1 < len(samples) else end
            lo, hi = max(a, t), min(b, t_next)
            if hi > lo:
                total += w * (hi - lo)
        out.append(round(total / width, 1))
    return out


def _alike(prog: dict[str, Any], minutes: float, kwh: float, sig: list[float]) -> float | None:
    """How far a run is from a program (lower is closer), None when not alike."""
    if not prog.get("min") or not prog.get("kwh"):
        return None
    dr, er = minutes / prog["min"], kwh / prog["kwh"]
    if not (0.75 <= dr <= 1.33 and 0.75 <= er <= 1.33):
        return None
    top = max(max(sig or [0]), max(prog.get("sig") or [0]), 1.0)
    diff = sum(abs(a - b) for a, b in zip(sig, prog.get("sig") or [0] * SIG_POINTS)) / SIG_POINTS / top
    if diff > 0.25:
        return None
    return diff + abs(1 - dr) + abs(1 - er)


KINDS = ("standby", "warm", "cool", "task")


def guess_kind(data: dict[str, Any]) -> str:
    """What kind of device: "standby" (only standby use: tv, NAS), "warm"
    (keeps something warm by itself: boiler, espresso), "cool" (fridge,
    freezer) or "task" (runs when started: dishwasher, washing machine).
    Short runs many times a day on their own: a thermostat (warm when it
    draws a lot, cool when little); a few longer runs: a task."""
    cycles = data.get("cycles") or []
    if not cycles:
        return "standby"
    first = dt_util.parse_datetime(cycles[0]["start"])
    days = max(1.0, (dt_util.utcnow() - first).total_seconds() / 86400) if first else 1.0
    per_day = len(cycles) / min(days, 30.0) if len(cycles) < 60 else len(cycles) / max(1.0, (
        dt_util.utcnow() - dt_util.parse_datetime(cycles[-60]["start"])).total_seconds() / 86400)
    minutes = sorted(c["min"] for c in cycles)
    median = minutes[len(minutes) // 2]
    if per_day >= 4 and median <= 60:
        return "warm" if (data.get("run_w") or 0) >= 500 else "cool"
    return "task"


class Learner:
    """One device's learning state (what is stored plus the run going on)."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data: dict[str, Any] = data or {}
        d = self.data
        d.setdefault("cycles", [])
        d.setdefault("programs", {})
        d.setdefault("heat", [[0] * 24 for _ in range(7)])
        d.setdefault("days", {})
        d.setdefault("months", {})
        d.setdefault("hours", {})
        d.setdefault("use", {})  # "YYYY-MM-DD": {"all": [quarters], "big": [quarters]}
        self.last: tuple[float, float] | None = None  # (timestamp, W)
        self.run: dict[str, Any] | None = None  # {"start", "kwh", "samples", "below"}

    def threshold(self) -> float:
        sb = self.data.get("standby")
        sb = 0.0 if sb is None else sb
        return max(sb + 15.0, sb * 1.5, 20.0)

    def _add_energy(self, t0: float, w0: float, t1: float) -> float:
        if t1 <= t0 or t1 - t0 > MAX_GAP:
            return 0.0
        kwh = w0 * (t1 - t0) / 3_600_000
        local = dt_util.as_local(dt_util.utc_from_timestamp(t0))
        days, months, hours = self.data["days"], self.data["months"], self.data["hours"]
        day, month, hour = local.strftime("%Y-%m-%d"), local.strftime("%Y-%m"), local.strftime("%Y-%m-%dT%H")
        days[day] = round(days.get(day, 0.0) + kwh, 5)
        hours[hour] = round(hours.get(hour, 0.0) + kwh, 6)
        months[month] = round(months.get(month, 0.0) + kwh, 5)
        return kwh

    def feed(self, t: float, w: float | None) -> dict[str, Any] | None:
        """A power reading (or the current value again, from the tick). Returns a finished run."""
        done = None
        if self.last is not None:
            t0, w0 = self.last
            kwh = self._add_energy(t0, w0, t)
            if self.run is not None:
                self.run["kwh"] += kwh
        if w is None:
            self.last = None
            return None
        th = self.threshold()
        if self.run is None:
            if w > th:
                self.run = {"start": t, "kwh": 0.0, "samples": [(t, w)], "below": None}
            else:
                sb = self.data.get("standby")
                self.data["standby"] = round(w if sb is None else sb + 0.05 * (w - sb), 2)
        else:
            if not self.run["samples"] or self.run["samples"][-1] != (t, w):
                self.run["samples"].append((t, w))
            if w <= th:
                if self.run["below"] is None:
                    self.run["below"] = t
                elif t - self.run["below"] >= END_IDLE:
                    done = self._finish(self.run["below"])
            else:
                self.run["below"] = None
        if self.last is None or self.last[0] != t or self.last[1] != w:
            self.last = (t, w)
        return done

    def _finish(self, end: float) -> dict[str, Any] | None:
        run, self.run = self.run, None
        if run is None:
            return None
        samples = [(t, w) for t, w in run["samples"] if t <= end]
        minutes = (end - run["start"]) / 60
        kwh = run["kwh"]
        if minutes < MIN_RUN_MIN or kwh < MIN_RUN_KWH or not samples:
            return None
        sig = _sig(samples, run["start"], end)
        progs = self.data["programs"]
        best, best_d = None, None
        for pid, prog in progs.items():
            d = _alike(prog, minutes, kwh, sig)
            if d is not None and (best_d is None or d < best_d):
                best, best_d = pid, d
        if best is None:
            n = 1
            while f"p{n}" in progs:
                n += 1
            best = f"p{n}"
            progs[best] = {"n": 0, "min": minutes, "kwh": kwh, "sig": sig}
        prog = progs[best]
        k = min(prog["n"], 49)
        prog["min"] = round((prog["min"] * k + minutes) / (k + 1), 2)
        prog["kwh"] = round((prog["kwh"] * k + kwh) / (k + 1), 4)
        prog["sig"] = [round((a * k + b) / (k + 1), 1) for a, b in zip(prog["sig"], sig)]
        prog["n"] += 1
        prog["last"] = dt_util.utc_from_timestamp(run["start"]).isoformat()
        local = dt_util.as_local(dt_util.utc_from_timestamp(run["start"]))
        self.data["heat"][local.weekday()][local.hour] += 1
        avg_w = kwh * 1000 / (minutes / 60)
        rw = self.data.get("run_w")
        self.data["run_w"] = round(avg_w if rw is None else rw + 0.2 * (avg_w - rw), 1)
        self.data["peak_w"] = round(max(self.data.get("peak_w") or 0.0, max(w for _, w in samples)), 1)
        self._mark_use(run["start"], end, kwh)
        cycle = {"start": dt_util.utc_from_timestamp(run["start"]).isoformat(), "min": round(minutes, 1),
                 "kwh": round(kwh, 4), "prog": best}
        self.data["cycles"] = [*self.data["cycles"], cycle][-MAX_CYCLES:]
        return cycle

    def _mark_use(self, start: float, end: float, kwh: float) -> None:
        """Note the quarters of the day this run covered: under "all", and under
        "big" when it used clearly more than a usual run (1.5× the median of the
        last 30; for a boiler or espresso: real use, not a keep-warm pulse)."""
        recent = sorted(c["kwh"] for c in self.data["cycles"][-30:])
        big = len(recent) < 5 or kwh > 1.5 * recent[len(recent) // 2]
        t = start - start % 900
        while t < end:
            local = dt_util.as_local(dt_util.utc_from_timestamp(t))
            day = self.data["use"].setdefault(local.strftime("%Y-%m-%d"), {"all": [], "big": []})
            q = local.hour * 4 + local.minute // 15
            for kind in ("all", "big") if big else ("all",):
                if q not in day[kind]:
                    day[kind].append(q)
            t += 900

    def prune(self) -> None:
        if self.data.get("use"):
            self.data["use"] = dict(sorted(self.data["use"].items())[-USE_DAYS:])
        for key, keep in (("days", DAYS_KEPT), ("months", MONTHS_KEPT), ("hours", DAYS_KEPT * 24)):
            items = sorted(self.data[key].items())
            self.data[key] = dict(items[-keep:])


class DeviceLearning:
    """Follows the power sensors of all metered switches and meters."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        self.learners: dict[str, Learner] = {}
        self.sensors: dict[str, str] = {}  # key → sensor
        self.names: dict[str, str] = {}
        self._unsubs: list[CALLBACK_TYPE] = []
        self._track: CALLBACK_TYPE | None = None
        self._booting: set[str] = set()
        self.on_done: Any = None  # called with (key, run) when a run is over (live, not when replaying history)

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        for key, value in (data.get("devices") or {}).items():
            if isinstance(value, dict):
                self.learners[key] = Learner(value)

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"devices": {k: l.data for k, l in self.learners.items()}}, 60)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(seconds=60)))
        self._sync()

    @callback
    def shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        if self._track:
            self._track()
            self._track = None
        self._save()

    def _devices(self) -> dict[str, tuple[str, str]]:
        """key → (sensor, name) of every metered switch and meter."""
        from .energy import room_parts  # noqa: PLC0415
        from .rooms import managed_areas  # noqa: PLC0415

        out: dict[str, tuple[str, str]] = {}
        managed = managed_areas(self.hass)
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            area = room.get("area_id")
            if area not in managed:
                continue
            try:
                parts = room_parts(self.hass, room)
            except Exception:  # noqa: BLE001 - a room that can't be read
                continue
            for part in parts:
                if part.get("kind") in ("switch", "meter") and part.get("sensor") and not part.get("hidden"):
                    out[f"{area}|{part['key']}"] = (part["sensor"], part.get("name") or part["key"])
        return out

    @callback
    def _sync(self, *_: Any) -> None:
        devices = self._devices()
        self.sensors = {k: s for k, (s, _n) in devices.items()}
        self.names = {k: n for k, (_s, n) in devices.items()}
        for key, sensor in self.sensors.items():
            learner = self.learners.get(key)
            if learner is not None and learner.data.get("sensor") != sensor:
                learner = None  # another sensor: start again
            if learner is None:
                learner = self.learners[key] = Learner({"sensor": sensor})
            if not learner.data.get("boot") and key not in self._booting:
                self._booting.add(key)
                self.hass.async_create_task(self._async_boot(key, sensor))
        if self._track:
            self._track()
            self._track = None
        if self.sensors:
            self._track = async_track_state_change_event(self.hass, sorted(set(self.sensors.values())), self._on_change)

    async def _async_boot(self, key: str, sensor: str) -> None:
        """Replay the history Home Assistant still has of this sensor."""
        try:
            from homeassistant.components.recorder import get_instance, history  # noqa: PLC0415

            end = dt_util.utcnow()
            start = end - timedelta(days=30)
            states = await get_instance(self.hass).async_add_executor_job(
                lambda: history.state_changes_during_period(self.hass, start, end, sensor, include_start_time_state=True)
            )
            rows = states.get(sensor, [])
        except Exception as err:  # noqa: BLE001 - no recorder, or it failed
            _LOGGER.debug("Device history for %s not read: %s", sensor, err)
            rows = []
        learner = self.learners.get(key)
        if learner is not None and learner.data.get("sensor") == sensor and not learner.data.get("boot"):
            for st in rows:
                learner.feed(st.last_updated.timestamp(), _watts(st))
            learner.data["boot"] = True
            learner.prune()
            self._save()
        self._booting.discard(key)

    @callback
    def _on_change(self, event: Event) -> None:
        from .const import energy_enabled  # noqa: PLC0415

        if not energy_enabled(self.hass):
            return
        sensor = event.data["entity_id"]
        new = event.data.get("new_state")
        t = (new.last_updated if new is not None else dt_util.utcnow()).timestamp()
        for key, s in self.sensors.items():
            if s == sensor and key not in self._booting and (learner := self.learners.get(key)) is not None:
                if (done := learner.feed(t, _watts(new))) is not None and self.on_done:
                    self.on_done(key, done)
        self._save()

    @callback
    def _tick(self, _now: Any = None) -> None:
        """The value as it is now: ends runs while the sensor does not change."""
        from .const import energy_enabled  # noqa: PLC0415

        if not energy_enabled(self.hass):
            return
        t = dt_util.utcnow().timestamp()
        for key, sensor in self.sensors.items():
            if key in self._booting or (learner := self.learners.get(key)) is None:
                continue
            if (done := learner.feed(t, _watts(self.hass.states.get(sensor)))) is not None and self.on_done:
                self.on_done(key, done)
            learner.prune()
        self._save()

    def forget(self, key: str) -> None:
        if key in self.learners:
            sensor = self.learners[key].data.get("sensor")
            self.learners[key] = Learner({"sensor": sensor, "boot": True})
            self._save()

    def profile(self, key: str) -> dict[str, Any] | None:
        """For the panel."""
        learner = self.learners.get(key)
        if learner is None:
            return None
        d = learner.data
        now = dt_util.now()
        week = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        since = (dt_util.utcnow() - timedelta(days=7)).isoformat()
        runs = [c for c in d["cycles"] if c["start"] >= since]
        months = sorted(d["months"].items())[-6:]
        return {
            "key": key, "name": self.names.get(key, key), "sensor": d.get("sensor"),
            "standby": d.get("standby"), "run_w": d.get("run_w"), "peak_w": d.get("peak_w"),
            "runs": len(d["cycles"]), "week_runs": len(runs),
            "week_kwh": round(sum(d["days"].get(day, 0.0) for day in week), 3),
            "programs": [
                {"id": pid, "n": p["n"], "min": p["min"], "kwh": p["kwh"], "sig": p["sig"], "last": p.get("last"),
                 "known": p["n"] >= PROGRAM_MIN}
                for pid, p in sorted(d["programs"].items(), key=lambda kv: -kv[1]["n"])
            ],
            "heat": d["heat"],
            "months": [{"month": m, "kwh": round(v, 3)} for m, v in months],
            "running": None if learner.run is None else {
                "since": dt_util.utc_from_timestamp(learner.run["start"]).isoformat(),
                "kwh": round(learner.run["kwh"], 3)},
            "boot": bool(d.get("boot")),
        }

    def profiles(self, area_id: str) -> list[dict[str, Any]]:
        return [p for key in self.sensors if key.startswith(f"{area_id}|") and (p := self.profile(key)) is not None]
