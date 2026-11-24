"""Does switching off pay? Per metered room switch (step 4 of the energy roadmap).

For every room switch with a power sensor (device_learning) RoomControl keeps:
- the buying price per local hour (from the price sensor; at startup also
  from its history in Home Assistant), the last 60 days;
- the switch's off periods: from when, until when, and why ("night",
  "nobody_home", "slot", "trial", … or "hand" when RoomControl did not do it);
  at startup also from the switch's history.

Per reason it compares each off period with the device's normal use per hour
of the day (learned on hours it was on and not just back on):
- saved: the normal use during the off hours × the price of those hours;
- catching up: the use above normal in the REBOUND_H hours after it came back
  on × the price of those hours (a boiler heating up again);
- net = saved − catching up, per time and per month, with a confidence.

For a device that keeps something warm (kind "warm") and has a "ready by"
time (room option power[part]["ready_by"]: "06:30") it advises when to
switch it back on: the cheapest moment that still leaves time to heat up.
"Apply" (panel) turns that into a time slot on the switch (room_switches
moment "slot").

A trial (power[part]["trial"] started from the panel) switches it off every
other night for TRIAL_NIGHTS nights, so there are nights with and without to
compare.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from statistics import median
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = "roomcontrol.offpay"
KEEP_DAYS = 60
REBOUND_H = 4
MIN_OFF_H = 1.0
TRIAL_NIGHTS = 14
TRIAL_OFF = "00:30"
DEFAULT_READY = "06:30"


def hour_key(when: datetime) -> str:
    return dt_util.as_local(when).strftime("%Y-%m-%dT%H")


def _hm(value: Any) -> tuple[int, int] | None:
    try:
        h, m = (int(x) for x in str(value).split(":")[:2])
    except ValueError:
        return None
    return (h, m) if 0 <= h < 24 and 0 <= m < 60 else None


class OffPay:
    def __init__(self, hass: HomeAssistant, learning: Any) -> None:
        self.hass = hass
        self.learning = learning
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        self.prices: dict[str, float] = {}
        self.periods: dict[str, list[dict[str, Any]]] = {}  # switch entity → periods
        self.trials: dict[str, dict[str, Any]] = {}  # device key → trial
        self.booted: list[str] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._track: CALLBACK_TYPE | None = None
        self._now_sum: tuple[str, float, int] | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.prices = {k: float(v) for k, v in (data.get("prices") or {}).items() if isinstance(v, (int, float))}
        self.periods = {k: list(v) for k, v in (data.get("periods") or {}).items() if isinstance(v, list)}
        self.trials = dict(data.get("trials") or {})
        self.booted = list(data.get("booted") or [])

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"prices": self.prices, "periods": self.periods,
                                              "trials": self.trials, "booted": self.booted}, 60)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._sync()
        self.hass.async_create_task(self._async_boot_prices())

    @callback
    def shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        if self._track:
            self._track()
            self._track = None
        self._save()

    # ── what to follow ─────────────────────────────────────────────────────

    def switches(self) -> dict[str, str]:
        """device key → switch entity, for metered room switches."""
        return {key: key.split("|switch:", 1)[1] for key in self.learning.sensors if "|switch:" in key}

    def _conf(self, key: str) -> dict[str, Any]:
        area, _, part = key.partition("|")
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == area:
                return (room.get("power") or {}).get(part) or {}
        return {}

    @callback
    def _sync(self, *_: Any) -> None:
        entities = sorted(set(self.switches().values()))
        if self._track:
            self._track()
            self._track = None
        if entities:
            self._track = async_track_state_change_event(self.hass, entities, self._on_switch)
        for entity in entities:
            if entity not in self.booted:
                self.booted.append(entity)
                self.hass.async_create_task(self._async_boot_switch(entity))

    # ── recording ──────────────────────────────────────────────────────────

    @callback
    def _on_switch(self, event: Event) -> None:
        old, new = event.data.get("old_state"), event.data.get("new_state")
        if old is None or new is None or old.state == new.state:
            return
        self._record(event.data["entity_id"], old.state, new.state, new.last_changed)
        self._save()

    def _record(self, entity: str, old: str, new: str, when: datetime, why: str | None = None) -> None:
        periods = self.periods.setdefault(entity, [])
        if old == "on" and new == "off":
            if why is None:
                why = (self.hass.data.get(DOMAIN, {}).get("switch_why") or {}).pop(entity, None) or "hand"
            periods.append({"off": when.isoformat(), "on": None, "why": why})
        elif new == "on" and periods and periods[-1].get("on") is None:
            periods[-1]["on"] = when.isoformat()
        since = (dt_util.utcnow() - timedelta(days=KEEP_DAYS)).isoformat()
        self.periods[entity] = [p for p in periods if (p.get("on") or "9") >= since][-400:]

    async def _async_history(self, entity: str, days: int = 30) -> list[Any]:
        try:
            from homeassistant.components.recorder import get_instance, history  # noqa: PLC0415

            end = dt_util.utcnow()
            states = await get_instance(self.hass).async_add_executor_job(
                lambda: history.state_changes_during_period(self.hass, end - timedelta(days=days), end, entity,
                                                            include_start_time_state=True))
            return states.get(entity, [])
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("History of %s not read: %s", entity, err)
            return []

    async def _async_boot_switch(self, entity: str) -> None:
        rows = await self._async_history(entity)
        prev = None
        known = {p["off"] for p in self.periods.get(entity, [])}
        for st in rows:
            if prev is not None and prev != st.state and st.last_changed.isoformat() not in known:
                self._record(entity, prev, st.state, st.last_changed, why="hand" if prev == "on" else None)
            prev = st.state
        self.periods.get(entity, []).sort(key=lambda p: p["off"])
        self._save()

    async def _async_boot_prices(self) -> None:
        sensor = (self.hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}).get("price_sensor")
        if not sensor:
            return
        sums: dict[str, list[float]] = {}
        for st in await self._async_history(sensor):
            try:
                value = float(st.state)
            except (TypeError, ValueError):
                continue
            value = value / 1e7 if abs(value) > 1000 else value / 100 if abs(value) > 5 else value
            sums.setdefault(hour_key(st.last_changed), []).append(value)
        for key, values in sums.items():
            self.prices.setdefault(key, round(sum(values) / len(values), 5))
        self._save()

    def _record_prices(self, now: datetime) -> None:
        from .tariff import buy_now, buy_rows  # noqa: PLC0415

        per_hour: dict[str, list[float]] = {}
        for r in buy_rows(self.hass):
            if r["start"] <= now:
                per_hour.setdefault(hour_key(r["start"]), []).append(r["price"])
        for key, values in per_hour.items():
            self.prices[key] = round(sum(values) / len(values), 5)
        key = hour_key(now)
        if key not in per_hour and (price := buy_now(self.hass)) is not None:
            k, total, n = self._now_sum if self._now_sum and self._now_sum[0] == key else (key, 0.0, 0)
            self._now_sum = (key, total + price, n + 1)
            self.prices[key] = round((total + price) / (n + 1), 5)
        cutoff = hour_key(now - timedelta(days=KEEP_DAYS))
        self.prices = {k: v for k, v in self.prices.items() if k >= cutoff}

    @callback
    def _tick(self, _now: Any = None) -> None:
        now = dt_util.utcnow()
        self._record_prices(now)
        self._run_trials(now)
        if now.minute == 5:
            self._auto_schedules(now)
        if now.minute == 0:
            self._save()

    # ── analysis ───────────────────────────────────────────────────────────

    def kind(self, key: str) -> tuple[str, bool]:
        """(kind, guessed): the user's choice, else the guess (fridge alarm on → cool)."""
        from .device_learning import KINDS, guess_kind  # noqa: PLC0415

        conf = self._conf(key)
        if conf.get("kind") in KINDS:
            return conf["kind"], False
        if (conf.get("watch") or {}).get("cool"):
            return "cool", True
        learner = self.learning.learners.get(key)
        return (guess_kind(learner.data) if learner else "standby"), True

    def _price(self, key: str, fallback: float | None) -> float | None:
        return self.prices.get(key, fallback)

    def analysis(self, key: str) -> dict[str, Any]:
        from .tariff import buy_now  # noqa: PLC0415

        entity = self.switches().get(key)
        learner = self.learning.learners.get(key)
        kind, guessed = self.kind(key)
        out: dict[str, Any] = {"kind": kind, "guessed": guessed, "reasons": [], "advice": None,
                               "trial": self._trial_status(key)}
        if not entity or learner is None:
            return out
        hours: dict[str, float] = learner.data.get("hours") or {}
        fallback = buy_now(self.hass)
        periods = [p for p in self.periods.get(entity, []) if p.get("on")]
        rebound_h = 0 if kind == "standby" else REBOUND_H
        # Hours that are off, or just back on: not "normal".
        special: set[str] = set()
        spans = []
        for p in periods:
            off, on = dt_util.parse_datetime(p["off"]), dt_util.parse_datetime(p["on"])
            if off is None or on is None or (on - off).total_seconds() < MIN_OFF_H * 3600:
                continue
            spans.append((p, off, on))
            t = off.replace(minute=0, second=0, microsecond=0)
            while t < on + timedelta(hours=rebound_h + 1):
                special.add(hour_key(t))
                t += timedelta(hours=1)
        by_hour: dict[int, list[float]] = {}
        for hk, kwh in hours.items():
            if hk not in special:
                by_hour.setdefault(int(hk[-2:]), []).append(kwh)
        base = {h: median(v) for h, v in by_hour.items() if len(v) >= 3}
        if not base:
            return out
        results: dict[str, list[dict[str, float]]] = {}
        for p, off, on in spans:
            saved_kwh = saved_eur = back_kwh = back_eur = 0.0
            t = off.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            complete = True
            while t + timedelta(hours=1) <= on:
                hk = hour_key(t)
                b = base.get(dt_util.as_local(t).hour)
                if b is None or hk not in hours:
                    complete = False
                    break
                gain = max(0.0, b - hours[hk])
                saved_kwh += gain
                saved_eur += gain * (self._price(hk, fallback) or 0.0)
                t += timedelta(hours=1)
            t = on.replace(minute=0, second=0, microsecond=0)
            for _ in range(rebound_h):
                hk = hour_key(t)
                b = base.get(dt_util.as_local(t).hour)
                if b is not None and hk in hours:
                    extra = max(0.0, hours[hk] - b)
                    back_kwh += extra
                    back_eur += extra * (self._price(hk, fallback) or 0.0)
                t += timedelta(hours=1)
            if not complete or (rebound_h and t > dt_util.utcnow()):
                continue
            results.setdefault(p["why"], []).append({
                "off": off.timestamp(), "on": on.timestamp(), "hours": (on - off).total_seconds() / 3600,
                "saved_kwh": saved_kwh, "saved": saved_eur, "back_kwh": back_kwh, "back": back_eur})
        month_ago = (dt_util.utcnow() - timedelta(days=30)).timestamp()
        for why, rows in sorted(results.items(), key=lambda kv: -len(kv[1])):
            n = len(rows)
            avg = {k: sum(r[k] for r in rows) / n for k in ("saved_kwh", "saved", "back_kwh", "back", "hours")}
            recent = [r for r in rows if r["on"] >= month_ago]
            first = min(r["off"] for r in rows)
            span_days = max(1.0, min(30.0, (dt_util.utcnow().timestamp() - first) / 86400))
            per_month = (avg["saved"] - avg["back"]) * len(recent) / span_days * 30
            out["reasons"].append({
                "why": why, "n": n, "hours": round(avg["hours"], 2),
                "saved_kwh": round(avg["saved_kwh"], 3), "saved": round(avg["saved"], 3),
                "back_kwh": round(avg["back_kwh"], 3), "back": round(avg["back"], 3),
                "net": round(avg["saved"] - avg["back"], 3), "per_month": round(per_month, 2),
                "confidence": "good" if n >= 10 else "fair" if n >= 5 else "low",
            })
        if kind == "warm":
            out["advice"] = self._advice(key, results, base, fallback)
        return out

    def _profile_prices(self, fallback: float | None) -> dict[int, float]:
        """The average price per hour of the day over the last 14 days."""
        cutoff = hour_key(dt_util.utcnow() - timedelta(days=14))
        per: dict[int, list[float]] = {}
        for hk, price in self.prices.items():
            if hk >= cutoff:
                per.setdefault(int(hk[-2:]), []).append(price)
        prof = {h: sum(v) / len(v) for h, v in per.items()}
        return {h: prof.get(h, fallback or 0.0) for h in range(24)}

    def _advice(self, key: str, results: dict[str, list[dict[str, float]]],
                base: dict[int, float], fallback: float | None) -> dict[str, Any] | None:
        """When to switch it back on: the cheapest moment that leaves time to heat up."""
        conf = self._conf(key)
        ready = _hm(conf.get("ready_by"))
        rows = [r for rs in results.values() for r in rs]
        if ready is None or not rows:
            return {"needs_ready": ready is None, "enough": bool(rows)} if ready is None or not rows else None
        hours_off = sum(r["hours"] for r in rows)
        loss = sum(r["back_kwh"] for r in rows) / hours_off if hours_off else 0.0  # kWh to catch up per hour off
        learner = self.learning.learners.get(key)
        run_kw = max(0.3, (learner.data.get("run_w") or 1000) / 1000) if learner else 1.0
        starts = sorted(dt_util.as_local(dt_util.utc_from_timestamp(r["off"])).hour * 60
                        + dt_util.as_local(dt_util.utc_from_timestamp(r["off"])).minute for r in rows)
        start_min = starts[len(starts) // 2]
        start_min = start_min if start_min >= 18 * 60 or start_min < 6 * 60 else 30  # an evening/night start, else 00:30
        ready_min = ready[0] * 60 + ready[1]
        prices = self._profile_prices(fallback)

        def minutes_between(a: int, b: int) -> int:
            return (b - a) % (24 * 60)

        window = minutes_between(start_min, ready_min)
        best = None
        for step in range(0, window + 1, 15):
            on_min = (start_min + step) % (24 * 60)
            off_h = step / 60
            heat_kwh = loss * off_h
            heat_h = heat_kwh / run_kw
            if step + heat_h * 60 > window:
                continue
            saved = sum(base.get((start_min // 60 + i) % 24, 0.0) * prices[(start_min // 60 + i) % 24]
                        for i in range(int(off_h)))
            cost = heat_kwh * prices[on_min // 60]
            net = saved - cost
            if best is None or net > best["net"]:
                best = {"on": f"{on_min // 60:02d}:{on_min % 60:02d}", "net": net}
        if best is None:
            return None
        return {"off": f"{start_min // 60:02d}:{start_min % 60:02d}", "on": best["on"],
                "net_day": round(best["net"], 3), "per_month": round(best["net"] * 30, 2),
                "ready_by": conf.get("ready_by")}

    # ── usage schedule, kept up to date (usage.py) ─────────────────────────

    def _auto_schedules(self, now: datetime) -> None:
        """Once a week: switches set to "auto_schedule" get the usage proposal as their slots."""
        from .usage import usage  # noqa: PLC0415

        week = dt_util.as_local(now).strftime("%G-W%V")
        rooms = self.hass.data.get(DOMAIN, {}).get("rooms", [])
        changed = False
        new_rooms = []
        for room in rooms:
            power = room.get("power") or {}
            switches = list(room.get("switches") or [])
            for i, sw in enumerate(switches):
                if not isinstance(sw, dict):
                    continue
                part = f"switch:{sw.get('entity_id')}"
                key = f"{room.get('area_id')}|{part}"
                learner = self.learning.learners.get(key)
                if not (power.get(part) or {}).get("auto_schedule") or learner is None:
                    continue
                if learner.data.get("auto_week") == week:
                    continue
                learner.data["auto_week"] = week
                result = usage(self, key)
                if not result or not result.get("enough") or not result.get("proposal"):
                    continue
                off_on = sw.get("off_on") if isinstance(sw.get("off_on"), list) else ["all_off", "nobody_home", "smoke"]
                new = {**sw, "off_on": [m for m in off_on if m not in ("slot", "night")] + ["slot"],
                       "slots": result["proposal"]}
                if new != sw:
                    switches[i] = new
                    changed = True
                    light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(room.get("area_id"))
                    if light is not None and hasattr(light, "_debug"):
                        st = self.hass.states.get(sw.get("entity_id"))
                        light._debug.append({"at": now.isoformat(), "kind": "info", "reason": "usage_schedule",
                                             "bundles": [(st.attributes.get("friendly_name") if st else None) or sw.get("entity_id")],
                                             "items": [sw.get("entity_id")]})
            new_rooms.append({**room, "switches": switches} if changed and switches != room.get("switches") else room)
        if changed:
            from . import _async_save  # noqa: PLC0415

            self.hass.async_create_task(_async_save(self.hass, rooms=new_rooms))

    # ── trial ──────────────────────────────────────────────────────────────

    def start_trial(self, key: str) -> None:
        conf = self._conf(key)
        self.trials[key] = {"started": dt_util.now().date().isoformat(),
                            "on": conf.get("ready_by") or DEFAULT_READY, "off_now": False}
        self._save()

    def stop_trial(self, key: str) -> None:
        trial = self.trials.pop(key, None)
        if trial and trial.get("off_now") and (entity := self.switches().get(key)):
            from .room_switches import async_turn  # noqa: PLC0415

            self.hass.async_create_task(async_turn(self.hass, [entity], True))
        self._save()

    def _trial_status(self, key: str) -> dict[str, Any] | None:
        trial = self.trials.get(key)
        if not trial:
            return None
        start = datetime.fromisoformat(trial["started"]).date()
        night = (dt_util.now().date() - start).days + 1
        return {"night": min(night, TRIAL_NIGHTS), "of": TRIAL_NIGHTS, "on": trial["on"], "off": TRIAL_OFF}

    def _run_trials(self, now: datetime) -> None:
        from .room_switches import async_turn  # noqa: PLC0415

        local = dt_util.as_local(now)
        off_at, on_at = _hm(TRIAL_OFF), None
        for key, trial in list(self.trials.items()):
            entity = self.switches().get(key)
            if entity is None:
                continue
            start = datetime.fromisoformat(trial["started"]).date()
            on_at = _hm(trial.get("on")) or _hm(DEFAULT_READY)
            minute = local.hour * 60 + local.minute
            in_window = off_at[0] * 60 + off_at[1] <= minute < on_at[0] * 60 + on_at[1]
            night = (local.date() - start).days
            if night >= TRIAL_NIGHTS and not trial.get("off_now"):
                self.trials.pop(key, None)  # done
                self._save()
                continue
            st = self.hass.states.get(entity)
            if in_window and night % 2 == 0 and not trial.get("off_now") and trial.get("last") != local.date().isoformat():
                if st is not None and st.state == "on":
                    trial["off_now"] = True
                    trial["last"] = local.date().isoformat()
                    self.hass.data.setdefault(DOMAIN, {}).setdefault("switch_why", {})[entity] = "trial"
                    self.hass.async_create_task(async_turn(self.hass, [entity], False))
                    self._save()
            elif not in_window and trial.get("off_now"):
                trial["off_now"] = False
                self.hass.async_create_task(async_turn(self.hass, [entity], True))
                self._save()
