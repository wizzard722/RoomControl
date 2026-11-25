"""Planning (energy step 5a): flexible devices at the cheapest, cleanest or sunniest time.

Inside the general setting "energy":
 "charger_entity": switch / input_boolean / number,  # the charging station, if it can
                                                     # be switched (a number: the charging
                                                     # current, max = on, min = off)
 "plan_on": "price" | "co2" | "both",                # what "best" means
 "co2_sensor": sensor,                               # g CO2 per kWh (Electricity Maps /
                                                     # CO2 Signal); hours ahead come from
                                                     # its "forecast" attribute, else from
                                                     # what it showed per hour of the day
 "plan": {"car" | "sw:<switch>": {"auto": bool,     # RoomControl switches it (else advice)
                               "mode": "cheap" | "sun",
                               "planned": true,      # a room switch chosen for planning
                               "kind": "warm" | "timer" | "charge" | "task" | "use",
                               "slots": [slot],      # "use": on during these time slots
                                                     # (light-bundle slot format)
                               "lead": min,          # "use": on this many minutes earlier
                               "watts": n,           # its power (default: learned / the room's)
                               "ready": "HH:MM",     # old: ready by; now only the fallback
                                                     # while the need is not learned yet
                               "hours": h,           # keeps warm: hours a day
                               "kwh": n}}            # the car: kWh a charge (default:
                                                     # from the battery level, else the
                                                     # median of the last charges)

Devices:
- the car: switched only when a charging station is chosen, else advice;
- the room switches the user chose (Energy → Planning → Add): "warm" keeps
  something warm (hours a day), "timer" is on for a while in the best
  stretch (the device starts when it gets power), "charge" needs kWh, and
  "task" (dishwasher, washing machine) runs its usual program in the best
  stretch (the plug stays off until then), and "use" (coffee maker) is on
  during the user's time slots and off in between (no price planning: it
  uses power when it is used); RoomControl proposes the slots from its
  learned use (usage.py).
- the home battery is no longer part of RoomControl (battery.py is not started).
"auto" on: RoomControl switches the device; off: advice only (the best stretch
is shown). Old settings without "auto": mode "cheap" or "sun" means on.
The ready time is predicted (need.py): per weekday when the device is usually
first needed, learned from its use (not the stretches RoomControl ran), from
switching it on by hand while planning held it off, and for the car from
unplugging it. Per window (up to the next need) a device in "cheap" gets the
best unbroken stretch of its hours; "sun" runs while the own surplus covers
half its power, and with a ready time the best stretch fills in the hours
the sun is not expected to give. RoomControl switches only when its wish
changes (switching by hand in between is left alone). The car is let finish:
still charging at the end of its stretch, the station stays on until it stops.

"What it brings": each stretch run is noted with its cost and with what the
same kWh would have cost at the window's average price.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

Q = timedelta(minutes=15)
DEFAULT_WARM_HOURS = 3.0
SUN_ON = 0.5  # share of its power the surplus must cover to switch on
SUN_OFF = 0.2
MIN_SWITCH = timedelta(minutes=5)
MODES = ("cheap", "sun")
SWITCH_KINDS = ("warm", "timer", "charge", "task", "use")
PLAN_ON = ("price", "co2", "both")
KEEP_RUNS = 400


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}


def _num(value: Any, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def _short_often(cycles: list[dict[str, Any]]) -> bool:
    """Used briefly, several times a day (coffee maker): runs of at most 15 minutes
    (median), on average at least 2 a day over the last two weeks."""
    since = (dt_util.utcnow() - timedelta(days=14)).isoformat()
    recent = [c for c in cycles if isinstance(c, dict) and str(c.get("start") or "") >= since]
    if len(recent) < 10:
        return False
    minutes = sorted(c.get("min") or 0 for c in recent)
    return minutes[len(minutes) // 2] <= 15 and len(recent) / 14 >= 2


def auto_of(conf: dict[str, Any]) -> bool:
    """Does RoomControl switch it? Old settings: mode cheap or sun."""
    if isinstance(conf.get("auto"), bool):
        return conf["auto"]
    return conf.get("mode") in MODES


class Planner:
    """Plans and switches the flexible devices."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.plan")
        self.runs: list[dict[str, Any]] = []
        self.co2: dict[str, float] = {}  # hour of the day → g/kWh (learned)
        self.done: dict[str, str] = {}  # key → window end (iso) whose stretch has run
        self.plans: dict[str, dict[str, Any]] = {}
        self._want: dict[str, bool] = {}  # key → what RoomControl last wanted
        self._switched: dict[str, datetime] = {}
        self._running: dict[str, dict[str, Any]] = {}  # key → the stretch being run
        self._finishing: set[str] = set()  # the car: let it finish
        self._unsubs: list[CALLBACK_TYPE] = []
        self._planned_at: datetime | None = None
        self.needs: dict[str, list[str]] = {}  # key → moments it was needed (switched on by hand, unplugged)
        self.blocks: dict[str, list[list[str]]] = {}  # key → the stretches RoomControl ran
        self._held: set[str] = set()  # switched on by hand while held off (noted once)
        self._plugged: bool | None = None
        self.sun_run: dict[str, dict[str, Any]] = {}  # key → {"window": iso, "min": minutes on the sun}
        self._was_on: dict[str, bool] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.runs = [r for r in data.get("runs") or [] if isinstance(r, dict)]
        self.co2 = {str(k): float(v) for k, v in (data.get("co2") or {}).items() if isinstance(v, (int, float))}
        self.done = {k: v for k, v in (data.get("done") or {}).items() if isinstance(v, str)}
        self._running = {k: v for k, v in (data.get("running") or {}).items() if isinstance(v, dict)}
        self.needs = {k: [x for x in v if isinstance(x, str)] for k, v in (data.get("needs") or {}).items() if isinstance(v, list)}
        self.blocks = {k: [b for b in v if isinstance(b, list) and len(b) == 2] for k, v in (data.get("blocks") or {}).items()
                       if isinstance(v, list)}
        self.sun_run = {k: v for k, v in (data.get("sun_run") or {}).items() if isinstance(v, dict)}

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"runs": self.runs[-KEEP_RUNS:], "co2": self.co2, "done": self.done,
                                              "running": self._running, "needs": self.needs, "blocks": self.blocks,
                                              "sun_run": self.sun_run}, 30)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._replan))

    @callback
    def shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []

    @callback
    def _replan(self, *_: Any) -> None:
        self._planned_at = None
        self._tick()

    # ── devices ────────────────────────────────────────────────────────────

    def _conf(self, key: str) -> dict[str, Any]:
        conf = (_cfg(self.hass).get("plan") or {}).get(key)
        return conf if isinstance(conf, dict) else {}

    def _car_kwh(self, cfg: dict[str, Any]) -> float:
        conf = self._conf("car")
        if isinstance(conf.get("kwh"), (int, float)) and conf["kwh"] > 0:
            return float(conf["kwh"])
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        battery = _num(cfg.get("battery_kwh"), 8.8)
        car = ((getattr(energy, "last_status", None) or {}).get("car") or {}) if energy else {}
        if car.get("soc_est") is not None:
            return max(0.0, (100 - car["soc_est"]) / 100 * battery)
        sessions = [s.get("kwh") for s in (getattr(energy, "sessions", None) or [])[-10:] if isinstance(s.get("kwh"), (int, float))]
        if sessions:
            return sorted(sessions)[len(sessions) // 2]
        return battery / 2

    def devices(self) -> list[dict[str, Any]]:
        """The devices that can be planned (or advised)."""
        from .room_switches import room_switches  # noqa: PLC0415

        hass = self.hass
        cfg = _cfg(hass)
        out: list[dict[str, Any]] = []
        if cfg.get("charger_room") or cfg.get("soc_sensor") or cfg.get("charger_entity"):
            kw = _num(cfg.get("charger_max_kw"), 3.7)
            kwh = self._car_kwh(cfg)
            out.append({"key": "car", "kind": "car", "name": (cfg.get("car_name") or "").strip() or None,
                        "entity": cfg.get("charger_entity") or None, "kw": kw, "kwh": round(kwh, 1),
                        "hours": round(kwh / kw, 2) if kw > 0 else 0.0, "area": cfg.get("charger_room")})
        for sw in self.switches():
            if not sw["planned"]:
                continue
            conf = self._conf(sw["key"])
            kind = conf.get("kind") if conf.get("kind") in SWITCH_KINDS else "warm"
            kw = sw["kw"]
            if kind == "use":
                hours, kwh = 0.0, 0.0
            elif kind == "task":
                hours = _num(conf.get("hours"), sw["task_hours"] or 2.0)
                kwh = sw["task_kwh"] if sw["task_kwh"] else kw * hours
            elif kind == "charge":
                kwh = _num(conf.get("kwh"), 2.0)
                hours = kwh / kw if kw > 0 else 0.0
            else:  # warm, timer: hours a day / how long it must be on
                hours = _num(conf.get("hours"), DEFAULT_WARM_HOURS if kind == "warm" else 1.5)
                kwh = kw * hours
            out.append({"key": sw["key"], "kind": kind, "name": sw["name"], "entity": sw["entity"],
                        "kw": round(kw, 3), "kwh": round(kwh, 2), "hours": round(hours, 2), "area": sw["area"],
                        "meter": sw["meter"], "learn_key": sw["learn_key"]})
        return out

    def switches(self) -> list[dict[str, Any]]:
        """Every switch set up in a room (that RoomControl may switch off), with
        its power: the user's watts, else what was learned, else the room's
        power setting, else 1 kW. "planned": chosen in Energy → Planning."""
        from .energy import room_parts  # noqa: PLC0415
        from .room_switches import room_switches  # noqa: PLC0415
        from .rooms import managed_areas  # noqa: PLC0415

        hass = self.hass
        plan = _cfg(hass).get("plan") or {}
        offpay = hass.data.get(DOMAIN, {}).get("offpay")
        learners = getattr(getattr(offpay, "learning", None), "learners", {}) or {}
        out = []
        managed = managed_areas(hass)
        for room in hass.data.get(DOMAIN, {}).get("rooms", []):
            area = room.get("area_id")
            if area not in managed:
                continue
            try:
                parts = {p["key"]: p for p in room_parts(hass, room)}
            except Exception:  # noqa: BLE001
                parts = {}
            for sw in room_switches(room):
                entity = sw["entity_id"]
                if not sw["may_off"]:
                    continue
                key = f"sw:{entity}"
                conf = plan.get(key) if isinstance(plan.get(key), dict) else {}
                part = parts.get(f"switch:{entity}") or {}
                learner = learners.get(f"{area}|switch:{entity}")
                data = learner.data if learner else {}
                power_conf = ((room.get("power") or {}).get(f"switch:{entity}") or {})
                watts = (_num(conf.get("watts"), 0.0) or _num(data.get("run_w"), 0.0)
                         or _num(power_conf.get("watts"), 0.0) or 1000.0)
                cycles = data.get("cycles") or []
                minutes = sorted(c["min"] for c in cycles[-20:])
                kwhs = sorted(c["kwh"] for c in cycles[-20:])
                st = hass.states.get(entity)
                out.append({"key": key, "entity": entity, "area": area, "learn_key": f"{area}|switch:{entity}",
                            "name": (st.attributes.get("friendly_name") if st else None) or entity,
                            "kw": watts / 1000, "meter": bool(part.get("sensor")),
                            "task_hours": minutes[len(minutes) // 2] / 60 if minutes else None,
                            "task_kwh": kwhs[len(kwhs) // 2] if kwhs else None,
                            "planned": bool(conf.get("planned"))})
        return out

    def need(self, key: str, kind: str, learn_key: str | None) -> dict[str, Any]:
        """When it is needed (need.py), with the next moment."""
        from .need import DEFAULT_Q, first_uses, next_need, predict  # noqa: PLC0415

        offpay = self.hass.data.get(DOMAIN, {}).get("offpay")
        learners = getattr(getattr(offpay, "learning", None), "learners", {}) or {}
        learner = learners.get(learn_key) if learn_key else None
        use = (learner.data.get("use") if learner else None) or {}
        which = "big" if kind == "warm" else "all"
        blocks = self.blocks.get(key, [])
        firsts = first_uses(use, which, blocks, self.needs.get(key, []))
        out = predict(firsts, use, which, blocks)
        ready = self._conf(key).get("ready") or (_cfg(self.hass).get("ready_by") if key == "car" else None)
        fallback = DEFAULT_Q
        if isinstance(ready, str) and ":" in ready:
            try:
                h, m = (int(x) for x in ready.split(":")[:2])
                fallback = (h % 24) * 4 + (m % 60) // 15
            except ValueError:
                pass
        at, learned = next_need(out["week"], dt_util.utcnow(), fallback)
        return {**out, "at": at, "at_learned": learned, "fallback_q": fallback, "meter": learner is not None}

    def _sun_done(self, key: str, window_end: datetime) -> float:
        """Hours it ran on the sun for this window (since the previous need): a boiler keeps that heat."""
        got = self.sun_run.get(key) or {}
        return got.get("min", 0) / 60 if got.get("window") == window_end.isoformat() else 0.0

    def _note_need(self, key: str, now: datetime) -> None:
        from .need import prune  # noqa: PLC0415

        self.needs[key] = prune([*self.needs.get(key, []), now.isoformat()], now)[-200:]
        self._planned_at = None
        self._save()

    # ── prices, sun, CO2 per quarter ───────────────────────────────────────

    def _co2_forecast(self) -> dict[datetime, float]:
        sensor = _cfg(self.hass).get("co2_sensor")
        st = self.hass.states.get(sensor) if sensor else None
        out: dict[datetime, float] = {}
        rows = st.attributes.get("forecast") if st is not None else None
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                when = dt_util.parse_datetime(str(r.get("datetime") or r.get("start") or ""))
                value = next((r[k] for k in ("carbon_intensity", "value", "co2", "intensity") if isinstance(r.get(k), (int, float))), None)
                if when is not None and value is not None:
                    out[dt_util.as_utc(when)] = float(value)
        return out

    def co2_at(self, when: datetime, fc: dict[datetime, float]) -> float | None:
        if fc:
            best = None
            for t, v in fc.items():
                if t <= when and (best is None or t > best[0]):
                    best = (t, v)
            if best is not None and when - best[0] < timedelta(hours=2):
                return best[1]
        hour = str(dt_util.as_local(when).hour)
        if hour in self.co2:
            return self.co2[hour]
        sensor = _cfg(self.hass).get("co2_sensor")
        st = self.hass.states.get(sensor) if sensor else None
        try:
            return float(st.state) if st is not None else None
        except (TypeError, ValueError):
            return None

    def quarters(self, until: datetime) -> list[dict[str, Any]]:
        """From now to `until`, per quarter: buy and sell price, expected sun, CO2."""
        from .solar_forecast import sun_kw_at  # noqa: PLC0415
        from .tariff import buy_now, forecast  # noqa: PLC0415

        now = dt_util.utcnow()
        start = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
        fc = forecast(self.hass)
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        sun = getattr(energy, "sun", None) or []
        co2 = self._co2_forecast()
        fixed = buy_now(self.hass)
        out = []
        t = start
        while t < until:
            row = next((r for r in fc if r["start"] <= t < r["end"]), None)
            out.append({"start": t, "end": t + Q,
                        "buy": row["buy"] if row else fixed, "sell": (row or {}).get("sell"),
                        "sun_kw": sun_kw_at(sun, t, t + Q) if sun else 0.0,
                        "co2": self.co2_at(t, co2)})
            t += Q
        return out

    def _scored(self, rows: list[dict[str, Any]], kw: float) -> list[dict[str, Any]]:
        """Rows with "price" = what to minimise: the price of a kWh for this
        device (own sun at the feed-in price), its CO2, or both (each scaled
        0–1 over the window, averaged)."""
        from .solar_forecast import DEFAULT_BASE_LOAD_W, grid_share  # noqa: PLC0415

        cfg = _cfg(self.hass)
        on = cfg.get("plan_on") if cfg.get("plan_on") in PLAN_ON else "price"
        if on != "price" and not cfg.get("co2_sensor"):
            on = "price"
        base_kw = _num(cfg.get("base_load_w"), DEFAULT_BASE_LOAD_W) / 1000
        eff = []
        for r in rows:
            share = grid_share(r["sun_kw"], base_kw, kw) if r["sun_kw"] else 1.0
            buy = r["buy"]
            price = None if buy is None else buy * share + (r["sell"] or 0.0) * (1 - share)
            co2 = None if r["co2"] is None else r["co2"] * share
            eff.append((price, co2))

        def scale(values: list[float | None]) -> list[float | None]:
            known = [v for v in values if v is not None]
            if not known:
                return values
            lo, hi = min(known), max(known)
            return [None if v is None else (0.5 if hi == lo else (v - lo) / (hi - lo)) for v in values]

        if on == "price":
            score = [p for p, _c in eff]
        elif on == "co2":
            score = [c for _p, c in eff]
        else:
            ps, cs = scale([p for p, _c in eff]), scale([c for _p, c in eff])
            score = [None if p is None and c is None else ((p if p is not None else 0.5) + (c if c is not None else 0.5)) / 2
                     for p, c in zip(ps, cs, strict=True)]
        return [{**r, "price": s} for r, s in zip(rows, score, strict=True) if s is not None]

    # ── planning ───────────────────────────────────────────────────────────

    def _surplus_w(self) -> float | None:
        """Own power to spare now: returned − consumed over all phases (W)."""
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        detail = ((getattr(energy, "last_status", None) or {}).get("phase_detail") or {}) if energy else {}
        if not detail:
            return None
        used = [d.get("consumed") for d in detail.values()]
        back = [d.get("produced") or 0 for d in detail.values()]
        if any(u is None for u in used):
            return None
        return sum(back) - sum(used)

    def _plan_one(self, dev: dict[str, Any], now: datetime) -> dict[str, Any]:
        from .ev import avg_over, cheapest  # noqa: PLC0415
        from .solar_forecast import DEFAULT_BASE_LOAD_W  # noqa: PLC0415

        key = dev["key"]
        conf = self._conf(key)
        if dev["kind"] == "use":
            return self._plan_use(dev, conf, now)
        mode = conf.get("mode") if conf.get("mode") in MODES else "cheap"
        auto = auto_of(conf)
        controllable = bool(dev.get("entity"))
        mode_used = mode if controllable and auto else "advice"
        need = self.need(key, dev["kind"], dev.get("learn_key"))
        end = need["at"]
        suggest = None
        if dev["kind"] != "car":
            from .need import SUGGEST_DAYS, accepted_week, next_set, suggestion  # noqa: PLC0415

            taken = accepted_week(conf.get("need_ok"))
            suggest = suggestion(need, conf.get("need_ok"))
            if taken is None:
                # Not taken over yet: RoomControl learns and leaves the device alone.
                return {"key": key, "mode": mode, "mode_used": "learning", "auto": auto, "controllable": controllable,
                        "window_end": now.isoformat(), "suggest": suggest, "need_ok": None,
                        "need": {"at": None, "learned": False, "days": need["days"], "week": need["week"],
                                 "hours": need["hours"], "meter": need["meter"], "any": need["learned"],
                                 "min_days": SUGGEST_DAYS}}
            end = next_set(taken, now) or end
            need = {**need, "at_learned": True}
        running = self._running.get(key)
        if running and (r_end := dt_util.parse_datetime(running.get("window_end") or "")) is not None and r_end > now:
            end = r_end  # a stretch is running for this window: keep it
        plan: dict[str, Any] = {"key": key, "mode": mode, "mode_used": mode_used, "auto": auto,
                                "ready": dt_util.as_local(end).strftime("%H:%M"),
                                "window_end": end.isoformat(), "controllable": controllable,
                                "need": {"at": end.isoformat(), "learned": need["at_learned"], "days": need["days"],
                                         "week": need["week"], "hours": need["hours"], "meter": need["meter"],
                                         "any": need["learned"]},
                                "suggest": suggest, "need_ok": conf.get("need_ok") if dev["kind"] != "car" else None}
        if running and running.get("window_end") == end.isoformat():
            plan["block"] = {k: running[k] for k in ("start", "end", "avg") if k in running}
            return plan
        if self.done.get(key) == end.isoformat() and mode_used in ("cheap", "sun", "advice"):
            plan["done"] = True
            return plan
        rows = self.quarters(end)
        hours = dev["hours"]
        if mode_used == "sun":
            cfg = _cfg(self.hass)
            base_kw = _num(cfg.get("base_load_w"), DEFAULT_BASE_LOAD_W) / 1000
            sun_q = sum(1 for r in rows if r["sun_kw"] - base_kw >= SUN_ON * dev["kw"])
            plan["sun_hours"] = round(sun_q / 4, 2)
            done_h = self._sun_done(key, end) if dev["kind"] == "warm" else 0.0
            plan["sun_done"] = round(done_h, 2)
            hours = max(0.0, hours - sun_q / 4 - done_h)
        if hours <= 0 or not rows:
            return plan
        scored = self._scored(rows, dev["kw"])
        best = cheapest(scored, hours, now, end)
        if best is None:
            return plan
        buy_rows = [{"start": r["start"], "end": r["end"], "price": r["buy"]} for r in rows if r["buy"] is not None]
        avg = avg_over(buy_rows, best["start"], best["end"])
        window_avg = (sum(r["price"] for r in buy_rows) / len(buy_rows)) if buy_rows else None
        now_avg = avg_over(buy_rows, now, now + timedelta(hours=hours)) if buy_rows else None
        kwh = dev["kw"] * hours
        plan["block"] = {"start": best["start"].isoformat(), "end": best["end"].isoformat(),
                         "avg": None if avg is None else round(avg, 4),
                         "cost": None if avg is None else round(avg * kwh, 2),
                         "cost_now": None if now_avg is None else round(now_avg * kwh, 2),
                         "window_avg": None if window_avg is None else round(window_avg, 4),
                         "co2": None if not any(r["co2"] for r in rows) else round(
                             sum(r["co2"] or 0 for r in rows if best["start"] <= r["start"] < best["end"])
                             / max(1, sum(1 for r in rows if best["start"] <= r["start"] < best["end"])))}
        return plan

    # ── "use": on during the user's time slots ─────────────────────────────

    def _use_slots(self, conf: dict[str, Any]) -> list[dict[str, Any]]:
        from .slots import mode_slots  # noqa: PLC0415

        return mode_slots([x for x in conf.get("slots") or [] if isinstance(x, dict)],
                          self.hass.data.get(DOMAIN, {}).get("vacation"))

    def _use_on(self, slots: list[dict[str, Any]], lead_min: float, when: datetime,
                phase: str | None = None, sun_down: bool | None = None) -> bool:
        """Is one of the slots running at `when` (or within the lead time after it)?"""
        from .slots import slot_part  # noqa: PLC0415

        local = dt_util.as_local(when)
        if phase is None:
            from .switch import _sun_phase  # noqa: PLC0415

            phase, sun_down = _sun_phase(self.hass)
        moments = [local, local + timedelta(minutes=lead_min)] if lead_min > 0 else [local]
        return any(slot_part(x, t, phase, bool(sun_down)) is not None for x in slots for t in moments)

    def _use_next(self, slots: list[dict[str, Any]], lead_min: float, now: datetime) -> dict[str, str] | None:
        """The current or next stretch it is on (start, end), looked for in 5 minute steps up to 8 days;
        schemer / donker ahead are guessed from the hour (dark from 18:00 to 07:00)."""
        def guess(t: datetime) -> tuple[str, bool]:
            h = dt_util.as_local(t).hour
            return ("dark", True) if h >= 18 or h < 7 else ("light", False)

        step = timedelta(minutes=5)
        t = now.replace(minute=now.minute // 5 * 5, second=0, microsecond=0)
        start = None
        for i in range(8 * 288):
            at = now if i == 0 else t + step * i
            on = self._use_on(slots, lead_min, at, *guess(at)) if i else self._use_on(slots, lead_min, at)
            if on and start is None:
                start = at
            elif not on and start is not None:
                return {"start": start.isoformat(), "end": at.isoformat()}
        return {"start": start.isoformat(), "end": (t + step * 8 * 288).isoformat()} if start else None

    def _use_proposal(self, learn_key: str | None) -> list[dict[str, Any]]:
        """The usage windows learned per weekday (usage.py), as "use" time slots."""
        from .usage import usage  # noqa: PLC0415

        offpay = self.hass.data.get(DOMAIN, {}).get("offpay")
        learners = getattr(getattr(offpay, "learning", None), "learners", {}) or {}
        if offpay is None or not learn_key or learn_key not in learners:
            return []
        try:
            u = usage(offpay, learn_key) or {}
        except Exception:  # noqa: BLE001 - a proposal must never break planning
            return []
        if not u.get("enough"):
            return []
        out = []
        for g in u.get("groups") or []:
            for w in g.get("windows") or []:
                a, _sep, b = w.partition("–")
                if a and b and a != b:
                    out.append({"days": list(g["days"]), "start": {"type": "time", "time": a},
                                "end": {"type": "time", "time": b}})
        return out

    def _plan_use(self, dev: dict[str, Any], conf: dict[str, Any], now: datetime) -> dict[str, Any]:
        slots = self._use_slots(conf)
        lead = _num(conf.get("lead"), 0.0)
        controllable = bool(dev.get("entity"))
        auto = conf["auto"] if isinstance(conf.get("auto"), bool) else True
        nxt = self._use_next(slots, lead, now) if slots else None
        return {"key": dev["key"], "mode": "use", "mode_used": "use" if controllable and auto and slots else "advice", "auto": auto,
                "controllable": controllable, "lead": lead, "slots_count": len(slots),
                "window_end": (nxt or {}).get("end") or now.isoformat(),
                "block": nxt, "proposal": self._use_proposal(dev.get("learn_key")),
                "need": {"at": None, "learned": False, "days": (u := self.need(dev["key"], "use", dev.get("learn_key")))["days"],
                         "week": u["week"], "hours": u["hours"], "meter": u["meter"], "any": u["learned"]}}

    @callback
    def plan(self) -> None:
        now = dt_util.utcnow()
        try:
            self.plans = {d["key"]: {**self._plan_one(d, now), "device": d} for d in self.devices()}
        except Exception:  # noqa: BLE001 - planning must never break the rest
            _LOGGER.exception("Planning failed")
        self._planned_at = now

    # ── switching ──────────────────────────────────────────────────────────

    def _is_on(self, entity: str) -> bool | None:
        st = self.hass.states.get(entity)
        if st is None or st.state in ("unknown", "unavailable"):
            return None
        if entity.startswith(("number.", "input_number.")):
            try:
                return float(st.state) > float(st.attributes.get("min", 0) or 0)
            except (TypeError, ValueError):
                return None
        return st.state == "on"

    async def _switch(self, dev: dict[str, Any], on: bool, why: str) -> None:
        entity = dev["entity"]
        domain = entity.split(".", 1)[0]
        try:
            if domain in ("number", "input_number"):
                st = self.hass.states.get(entity)
                attrs = st.attributes if st is not None else {}
                value = attrs.get("max", 16) if on else attrs.get("min", 0)
                await self.hass.services.async_call(domain, "set_value", {"entity_id": entity, "value": value}, blocking=True)
            else:
                self.hass.data.setdefault(DOMAIN, {}).setdefault("switch_why", {})[entity] = "plan"
                await self.hass.services.async_call(domain if domain in ("switch", "input_boolean") else "homeassistant",
                                                    "turn_on" if on else "turn_off", {"entity_id": entity}, blocking=True)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Planning: could not switch %s: %s", entity, err)
            return
        light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(dev.get("area") or "")
        if light is not None and hasattr(light, "_debug"):
            light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": "on" if on else "off", "reason": f"plan_{why}",
                                 "bundles": [dev.get("name") or entity], "items": [entity]})

    def _note_run(self, key: str, dev: dict[str, Any], run: dict[str, Any], now: datetime) -> None:
        """A stretch has run: what it cost and what it would have cost at the window's average."""
        start = dt_util.parse_datetime(run.get("start") or "")
        if start is None:
            return
        hours = max(0.0, (now - start).total_seconds() / 3600)
        kwh = dev["kw"] * hours
        avg, window_avg = run.get("avg"), run.get("window_avg")
        self.runs.append({"at": now.isoformat(), "key": key, "kwh": round(kwh, 2),
                          "cost": None if avg is None else round(avg * kwh, 3),
                          "ref": None if window_avg is None else round(window_avg * kwh, 3)})

    @callback
    def _tick(self, _now: Any = None) -> None:
        from .const import energy_enabled  # noqa: PLC0415

        if not energy_enabled(self.hass):
            self._release()
            return
        now = dt_util.utcnow()
        cfg = _cfg(self.hass)
        self._learn_co2(now, cfg)
        if self._planned_at is None or now - self._planned_at >= timedelta(minutes=15):
            self.plan()
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        car = ((getattr(energy, "last_status", None) or {}).get("car") or {}) if energy else {}
        car_charging = bool(car.get("charging"))
        plugged = car.get("plugged")
        if self._plugged is True and plugged is False and "car" in self.plans:
            self._note_need("car", now)  # unplugged: the car was needed now
        if isinstance(plugged, bool):
            self._plugged = plugged
        for key, plan in list(self.plans.items()):
            dev = plan["device"]
            if plan["mode_used"] == "learning" and dev.get("entity"):
                on = self._is_on(dev["entity"])
                if on and self._was_on.get(key) is False and not dev.get("meter"):
                    self._note_need(key, now)  # switched on (no meter to learn from): needed now
                if on is not None:
                    self._was_on[key] = on
            if not plan.get("controllable") or plan["mode_used"] not in ("cheap", "sun", "use"):
                self._running.pop(key, None)
                if self._want.pop(key, None) is False and plan.get("controllable") and self._is_on(dev["entity"]) is False:
                    self.hass.async_create_task(self._switch(dev, True, "block"))  # no longer automatic: back on
                continue
            if plan["mode_used"] == "use":
                want = self._use_on(self._use_slots(self._conf(key)), _num(self._conf(key).get("lead"), 0.0), now)
                in_block = want
            else:
                block = plan.get("block")
                in_block = False
                if block:
                    b_start, b_end = dt_util.parse_datetime(block["start"]), dt_util.parse_datetime(block["end"])
                    in_block = b_start is not None and b_end is not None and b_start <= now < b_end
                    if in_block and key not in self._running:
                        self._running[key] = {**block, "window_end": plan["window_end"]}
                        from .need import prune  # noqa: PLC0415

                        self.blocks[key] = prune([*self.blocks.get(key, []), [block["start"], block["end"]]], now,
                                                 lambda b: b[1])[-200:]
                        self._save()
                if not in_block and key in self._running:
                    run = self._running.pop(key)
                    self._note_run(key, dev, run, now)
                    self.done[key] = run.get("window_end") or plan["window_end"]
                    if dev["kind"] == "car" and car_charging:
                        self._finishing.add(key)
                    self._save()
                    self._planned_at = None
                want = in_block
                if plan["mode_used"] == "sun" and not want:
                    surplus = self._surplus_w()
                    was = self._want.get(key, False)
                    own = dev["kw"] * 1000 if self._is_on(dev["entity"]) else 0.0
                    if surplus is not None:
                        spare = surplus + own
                        want = spare >= SUN_ON * dev["kw"] * 1000 if not was else spare >= SUN_OFF * dev["kw"] * 1000
                    else:
                        want = was
                    last = self._switched.get(key)
                    if want != was and last is not None and now - last < MIN_SWITCH:
                        want = was
            if plan["mode_used"] == "sun" and want and not in_block and self._is_on(dev["entity"]):
                run = self.sun_run.get(key) or {}
                if run.get("window") != plan["window_end"]:
                    run = {"window": plan["window_end"], "min": 0}
                run["min"] = run.get("min", 0) + 1  # one tick = one minute on the sun
                self.sun_run[key] = run
                if run["min"] % 15 == 0:
                    self._save()
                    self._planned_at = None
            if key in self._finishing:
                if car_charging:
                    want = True
                else:
                    self._finishing.discard(key)
            if self._want.get(key) is False and not want and key != "car" and dev["kind"] != "use":
                last = self._switched.get(key)
                if self._is_on(dev["entity"]) and (last is None or now - last >= timedelta(minutes=2)):
                    if key not in self._held:
                        self._held.add(key)
                        self._note_need(key, now)  # switched on by hand while held off: needed now
                else:
                    self._held.discard(key)
            else:
                self._held.discard(key)
            if self._want.get(key) == want and key in self._want:
                continue  # nothing new: what is switched by hand stays
            first = key not in self._want
            self._want[key] = want
            if first and self._is_on(dev["entity"]) == want:
                continue
            self._switched[key] = now
            self.hass.async_create_task(self._switch(dev, want, ("sun" if plan["mode_used"] == "sun" and not in_block else "block")
                                                     if want else "wait"))

    def _release(self) -> None:
        """Energy management switched off: what RoomControl held off goes back on."""
        for key, want in list(self._want.items()):
            plan = self.plans.get(key)
            if not want and plan and plan.get("controllable") and self._is_on(plan["device"]["entity"]) is False:
                self.hass.async_create_task(self._switch(plan["device"], True, "block"))
        self._want.clear()
        self._running.clear()
        self._finishing.clear()

    def _learn_co2(self, now: datetime, cfg: dict[str, Any]) -> None:
        sensor = cfg.get("co2_sensor")
        st = self.hass.states.get(sensor) if sensor else None
        try:
            value = float(st.state) if st is not None else None
        except (TypeError, ValueError):
            value = None
        if value is None or now.minute % 15:
            return
        hour = str(dt_util.as_local(now).hour)
        old = self.co2.get(hour)
        self.co2[hour] = round(value if old is None else old + 0.2 * (value - old), 1)
        self._save()

    # ── for the panel ──────────────────────────────────────────────────────

    def _candidates(self) -> list[dict[str, Any]]:
        """Room switches not planned yet: the recognised ones (with learned use) first,
        with the kind guessed from learning and when they would be needed."""
        from .need import fmt_q  # noqa: PLC0415

        offpay = self.hass.data.get(DOMAIN, {}).get("offpay")
        learners = getattr(getattr(offpay, "learning", None), "learners", {}) or {}
        out = []
        for sw in self.switches():
            if sw["planned"]:
                continue
            learner = learners.get(sw["learn_key"])
            guess = None
            if learner is not None and learner.data.get("cycles") and offpay is not None:
                guess = "use" if _short_often(learner.data.get("cycles") or []) else \
                    {"warm": "warm", "task": "task"}.get(offpay.kind(sw["learn_key"])[0], "timer")
            kind = guess or "timer"
            need = self.need(sw["key"], kind, sw["learn_key"])
            out.append({"key": sw["key"], "entity": sw["entity"], "area": sw["area"], "name": sw["name"],
                        "meter": sw["meter"], "watts": round(sw["kw"] * 1000), "kind": kind, "known": guess is not None,
                        "runs": len(learner.data.get("cycles") or []) if learner else 0,
                        "hours": round(sw["task_hours"], 2) if sw["task_hours"] else None,
                        "need": {"week": [fmt_q(w["q"]) if w["learned"] else None for w in need["week"]],
                                 "days": need["days"], "learned": need["learned"]},
                        "proposal": self._use_proposal(sw["learn_key"]) if kind == "use" else []})
        out.sort(key=lambda c: (not c["known"], -c["runs"], c["name"].lower()))
        return out

    def status(self) -> dict[str, Any]:
        now = dt_util.utcnow()
        if self._planned_at is None or now - self._planned_at >= timedelta(minutes=5):
            self.plan()
        cfg = _cfg(self.hass)
        rows = self.quarters(now + timedelta(hours=24))
        local = dt_util.as_local(now)
        month = local.strftime("%Y-%m")
        runs = [r for r in self.runs if dt_util.as_local(dt_util.parse_datetime(r["at"])).strftime("%Y-%m") == month]
        priced = [r for r in runs if r.get("cost") is not None and r.get("ref") is not None]
        devices = []
        for plan in self.plans.values():
            dev = plan["device"]
            devices.append({**{k: v for k, v in plan.items() if k != "device"}, **{k: dev[k] for k in (
                "kind", "name", "entity", "kw", "kwh", "hours")}, "area": dev.get("area"), "meter": dev.get("meter"),
                "watts_set": self._conf(dev["key"]).get("watts"),
                "on": self._is_on(dev["entity"]) if dev.get("entity") else None,
                "hours_set": self._conf(dev["key"]).get("hours"), "kwh_set": self._conf(dev["key"]).get("kwh")})
        battery = None
        hb = self.hass.data.get(DOMAIN, {}).get("battery")
        if hb is not None and hb.configured():
            bst = hb.status()
            if bst.get("strategy") and bst["strategy"] != "off":
                battery = {"soc": bst.get("soc"), "strategy": bst["strategy"], "plan": bst.get("plan") or [],
                           "blocks": [b for b in bst.get("blocks") or [] if b["action"] in ("charge", "discharge")]}
        return {
            "candidates": self._candidates(),
            "battery": battery,
            "plan_on": cfg.get("plan_on") if cfg.get("plan_on") in PLAN_ON else "price",
            "co2_sensor": cfg.get("co2_sensor") or None,
            "sun_missing": bool((en := self.hass.data.get(DOMAIN, {}).get("energy")) and hasattr(en, "sun_missing")
                                and en.sun_missing()),
            "charger": cfg.get("charger_entity") or None,
            "rows": [{"start": r["start"].isoformat(), "buy": None if r["buy"] is None else round(r["buy"], 4),
                      "sun_kw": round(r["sun_kw"], 2), "co2": None if r["co2"] is None else round(r["co2"])} for r in rows],
            "devices": devices,
            "savings": {"month": round(sum(r["ref"] - r["cost"] for r in priced), 2) if priced else None,
                        "runs": len(runs), "kwh": round(sum(r["kwh"] for r in runs), 1)},
        }
