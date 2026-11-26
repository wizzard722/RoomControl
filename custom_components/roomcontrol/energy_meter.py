"""Energy → Overzicht (step 7a): what the house uses, now and today, and where.

On every energy tick (energy.py, every 30 s) the power now is added up into
kWh: per room (its parts), the house (all phases), taken from and returned to
the grid, the solar panels, the car, and "not assigned" (the house minus the
rooms and the car). Per local day those kWh are kept with their cost (the
price you pay at that moment; what is returned at the feed-in price), for
400 days (store "roomcontrol.energy_meter"). Per room a running total feeds
the room's energy sensor (kWh, for Home Assistant's Energy dashboard →
Individual devices).

Base load ("sluipverbruik"): each night 03:00–05:00 the house's average
power and that of each metered part, the last 7 nights averaged.

General setting "energy" → "fuse_a": the main fuse per phase (default 25 A),
for the phase bars.

Energy → Rekening (step 7b), general setting "energy" → "bill":
 {"termijn": € a month (the advance payment),
  "fixed_month": € a month (standing charges, grid costs, minus the energy
                 tax rebate; may be negative),
  "gas_price": € per m³}
A month = electricity (per day: taken × the price then − returned × the
feed-in price then) + the fixed costs (per day of the month) + gas (the gas
meter of Home Assistant's Energy dashboard, m³ per day × the gas price).
The forecast for the whole month: so far plus the average day of the last
14 days for each day still to come.

Energy → Besparen (step 7c): per day also
- "idle": light bundles on while their room saw no motion for IDLE_MIN
  minutes (not while their own time slot runs, an alarm clock rings or the
  room is under manual control): kWh, € and how often ("n");
- "away": metered switches and meters using power while nobody is home:
  kWh, € and hours.
Energy → Overzicht 2: per day also
- "hours": per local hour (24 values each) the house, taken from and
  returned to the grid and the solar panels, in kWh; hours from before
  RoomControl counted are filled in from Home Assistant's Energy dashboard
  ("filled": those hours);
- "parts": per room part ("<area>|<key>": a light bundle, switch or meter)
  kWh, minutes on (>= 1 W) and how often it went on ("n").
Both are kept PARTS_DAYS days.
coach() turns a week of that into tips (with what they bring per week and,
where RoomControl can, a setting to apply), what went well and the cost per
room; dismissed tips are kept.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

SIGNAL_METER = f"{DOMAIN}_energy_meter"
IDLE_MIN = 60
KEEP_DAYS = 400
NIGHT = (3, 5)  # local hours of the base load window
VOLT = 230.0
DEFAULT_FUSE = 25.0
PARTS_DAYS = 8  # days that keep "hours" and "parts"
HOUR_KEYS = ("house", "grid_in", "grid_out", "solar")


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}


def _add(d: dict[str, float], key: str, value: float) -> None:
    d[key] = round(d.get(key, 0.0) + value, 5)


class EnergyMeter:
    """Adds the power of each energy tick up into kWh and cost per day."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.energy_meter")
        self.days: dict[str, dict[str, Any]] = {}
        self.totals: dict[str, float] = {}  # area → kWh ever (the room energy sensors)
        self.nights: dict[str, dict[str, Any]] = {}  # date → {"n", "house", "parts": {key: W}, "names"}
        self._last: datetime | None = None
        self._unsub: CALLBACK_TYPE | None = None
        self.dismissed: list[str] = []
        self._idle_flag: dict[str, bool] = {}
        self._part_on: dict[str, bool] = {}
        self._filled_day: str | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.days = {k: v for k, v in (data.get("days") or {}).items() if isinstance(v, dict)}
        self.totals = {k: float(v) for k, v in (data.get("totals") or {}).items() if isinstance(v, (int, float))}
        self.nights = {k: v for k, v in (data.get("nights") or {}).items() if isinstance(v, dict)}
        self.dismissed = [x for x in data.get("dismissed") or [] if isinstance(x, str)]

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"days": self.days, "totals": self.totals, "nights": self.nights,
                                              "dismissed": self.dismissed}, 120)

    @callback
    def start(self) -> None:
        from .energy import SIGNAL_ENERGY  # noqa: PLC0415

        self._unsub = async_dispatcher_connect(self.hass, SIGNAL_ENERGY, self._on_energy)

    @callback
    def shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ── adding up ──────────────────────────────────────────────────────────

    @callback
    def _on_energy(self, *_: Any) -> None:
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        status = getattr(energy, "last_status", None) if energy else None
        if status:
            self.add(status, dt_util.utcnow())

    def add(self, status: dict[str, Any], now: datetime) -> None:
        from .tariff import buy_now, sell_now  # noqa: PLC0415

        last, self._last = self._last, now
        if last is None:
            return
        hours = (now - last).total_seconds() / 3600
        if hours <= 0 or hours > 0.05:  # more than 3 minutes: a gap (restart), not counted
            return
        buy = buy_now(self.hass)
        sell = sell_now(self.hass)
        local = dt_util.as_local(now)
        day = self.days.setdefault(local.strftime("%Y-%m-%d"), {"rooms": {}, "rooms_cost": {}})
        rooms = status.get("rooms") or {}
        rooms_w = 0.0
        for area, r in rooms.items():
            w = r.get("watts") or 0.0
            rooms_w += w
            kwh = w / 1000 * hours
            _add(day["rooms"], area, kwh)
            if buy is not None:
                _add(day["rooms_cost"], area, kwh * buy)
            self.totals[area] = round(self.totals.get(area, 0.0) + kwh, 5)
        detail = status.get("phase_detail") or {}
        phases = [v for v in (status.get("phases") or {}).values() if v is not None]
        house_w = sum(phases) if phases and len(phases) == len(status.get("phases") or {}) else None
        car = status.get("car") or {}
        car_w = (car.get("kw") or 0.0) * 1000 if car.get("charging") else 0.0
        if house_w is not None:
            _add(day, "house", house_w / 1000 * hours)
            _add(day, "unassigned", max(0.0, house_w - rooms_w - car_w) / 1000 * hours)
            if buy is not None:
                _add(day, "house_cost", house_w / 1000 * hours * buy)
        if car_w:
            _add(day, "car", car_w / 1000 * hours)
        used = [d.get("consumed") for d in detail.values()]
        if used and all(u is not None for u in used):
            grid_in = sum(used) / 1000 * hours
            grid_out = sum(d.get("produced") or 0 for d in detail.values()) / 1000 * hours
            _add(day, "grid_in", grid_in)
            _add(day, "grid_out", grid_out)
            if buy is not None:
                _add(day, "cost_in", grid_in * buy)
            if sell is not None:
                _add(day, "earn_out", grid_out * sell)
        solar = [d.get("solar") for d in detail.values() if d.get("solar") is not None]
        if solar:
            _add(day, "solar", sum(solar) / 1000 * hours)
        self._waste(day, rooms, hours, buy, now)
        self._per_hour(day, local.hour, hours, house_w, detail, solar)
        self._per_part(day, rooms, hours, buy)
        self._per_outdoor(day, hours, buy, status)
        if NIGHT[0] <= local.hour < NIGHT[1] and house_w is not None:
            night = self.nights.setdefault(local.strftime("%Y-%m-%d"), {"n": 0, "house": 0.0, "parts": {}, "names": {}})
            n = night["n"]
            night["house"] = round((night["house"] * n + house_w) / (n + 1), 2)
            for area, r in rooms.items():
                for p in r.get("parts") or []:
                    if p.get("watts") is None or p.get("kind") not in ("switch", "meter", "bundle"):
                        continue
                    key = f"{area}|{p['key']}"
                    old = night["parts"].get(key, 0.0)
                    night["parts"][key] = round((old * n + p["watts"]) / (n + 1), 2)
                    night["names"][key] = p.get("name") or p["key"]
            night["n"] = n + 1
        if local.minute == 0 and local.second < 31:
            cutoff = (local - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
            self.days = {k: v for k, v in self.days.items() if k >= cutoff}
            ncut = (local - timedelta(days=14)).strftime("%Y-%m-%d")
            self.nights = {k: v for k, v in self.nights.items() if k >= ncut}
            pcut = (local - timedelta(days=PARTS_DAYS)).strftime("%Y-%m-%d")
            for k, v in self.days.items():
                if k < pcut:
                    for x in ("hours", "parts", "filled"):
                        v.pop(x, None)
        self._save()
        async_dispatcher_send(self.hass, SIGNAL_METER)

    def _waste(self, day: dict[str, Any], rooms: dict[str, Any], hours: float, buy: float | None, now: datetime) -> None:
        """Light in an empty room, and use while nobody is home."""
        from .rooms import anyone_home  # noqa: PLC0415

        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        names = day.setdefault("names", {})
        home = anyone_home(self.hass)
        for area, r in rooms.items():
            light = entities.get(area)
            for p in r.get("parts") or []:
                w = p.get("watts") or 0.0
                key = f"{area}|{p['key']}"
                if p.get("kind") == "bundle":
                    idle = False
                    if w >= 1 and light is not None and getattr(light, "_motion_sensors", None) and light._motion_sensors():
                        try:
                            quiet = now - light._last_motion_at >= timedelta(minutes=IDLE_MIN) and not light._any_motion()
                            lamps = self._bundle_lamps(area, p["key"])
                            held = set(light._own_active()) | set(light._clock_lamps())
                            idle = quiet and not light._manual and not (lamps & held)
                        except Exception:  # noqa: BLE001 - a room that can't be read now
                            idle = False
                    if idle:
                        rec = day.setdefault("idle", {}).setdefault(key, {"kwh": 0.0, "eur": 0.0, "n": 0})
                        rec["kwh"] = round(rec["kwh"] + w / 1000 * hours, 5)
                        rec["eur"] = round(rec["eur"] + (w / 1000 * hours * buy if buy is not None else 0.0), 5)
                        if not self._idle_flag.get(key):
                            rec["n"] += 1
                            self._idle_flag[key] = True
                        names[key] = p.get("name") or p["key"]
                    else:
                        self._idle_flag.pop(key, None)
                elif p.get("kind") in ("switch", "meter") and not home and w >= 1:
                    rec = day.setdefault("away", {}).setdefault(key, {"kwh": 0.0, "eur": 0.0, "h": 0.0, "w": 0.0})
                    rec["kwh"] = round(rec["kwh"] + w / 1000 * hours, 5)
                    rec["eur"] = round(rec["eur"] + (w / 1000 * hours * buy if buy is not None else 0.0), 5)
                    rec["h"] = round(rec["h"] + hours, 4)
                    rec["w"] = round(rec["kwh"] * 1000 / rec["h"], 1) if rec["h"] else w
                    names[key] = p.get("name") or p["key"]

    @staticmethod
    def _per_hour(day: dict[str, Any], hour: int, hours: float, house_w: float | None,
                  detail: dict[str, Any], solar: list[Any]) -> None:
        """kWh of this tick into the day's hour."""
        hrs = day.setdefault("hours", {})
        for k in HOUR_KEYS:
            if not isinstance(hrs.get(k), list) or len(hrs[k]) != 24:
                hrs[k] = [0.0] * 24
        if house_w is not None:
            hrs["house"][hour] = round(hrs["house"][hour] + house_w / 1000 * hours, 5)
        used = [d.get("consumed") for d in detail.values()]
        if used and all(u is not None for u in used):
            hrs["grid_in"][hour] = round(hrs["grid_in"][hour] + sum(used) / 1000 * hours, 5)
            hrs["grid_out"][hour] = round(hrs["grid_out"][hour] + sum(d.get("produced") or 0 for d in detail.values()) / 1000 * hours, 5)
        if solar:
            hrs["solar"][hour] = round(hrs["solar"][hour] + sum(solar) / 1000 * hours, 5)

    def _heaters(self) -> set[str]:
        """"<area>|switch:<entity>" of the room switches of kind "heater"."""
        from .room_switches import room_switches  # noqa: PLC0415

        return {f"{r.get('area_id')}|switch:{sw['entity_id']}" for r in self.hass.data.get(DOMAIN, {}).get("rooms", [])
                for sw in room_switches(r) if sw["kind"] == "heater"}

    def _per_part(self, day: dict[str, Any], rooms: dict[str, Any], hours: float, buy: float | None = None) -> None:
        """kWh, minutes on and switch-ons of each room part; heaters also into
        "heat" (kWh and €, kept as long as the day)."""
        parts = day.setdefault("parts", {})
        names = day.setdefault("names", {})
        heaters = self._heaters()
        for area, r in rooms.items():
            for p in r.get("parts") or []:
                if p.get("kind") not in ("bundle", "switch", "meter", "ac") or p.get("watts") is None:
                    continue
                key = f"{area}|{p['key']}"
                w = p["watts"] or 0.0
                on = w >= 1
                rec = parts.setdefault(key, {"kwh": 0.0, "min": 0.0, "n": 0})
                rec["kwh"] = round(rec["kwh"] + w / 1000 * hours, 5)
                if key in heaters and w > 0:
                    heat = day.setdefault("heat", {}).setdefault(key, {"kwh": 0.0, "eur": 0.0})
                    heat["kwh"] = round(heat["kwh"] + w / 1000 * hours, 5)
                    if buy is not None:
                        heat["eur"] = round(heat["eur"] + w / 1000 * hours * buy, 5)
                if on:
                    rec["min"] = round(rec["min"] + hours * 60, 3)
                    if self._part_on.get(key) is False:
                        rec["n"] += 1
                    elif key not in self._part_on and rec["n"] == 0:
                        rec["n"] = 1
                self._part_on[key] = on
                names[key] = p.get("name") or p["key"]

    async def async_fill_hours(self) -> None:
        """Today's hours from before RoomControl counted, from the Energy
        dashboard's hourly statistics (grid in and out, solar)."""
        now = dt_util.as_local(dt_util.utcnow())
        key = now.strftime("%Y-%m-%d")
        if self._filled_day == key:
            return
        self._filled_day = key
        try:
            from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

            manager = await async_get_manager(self.hass)
            sources = (manager.data or {}).get("energy_sources") or []
        except Exception:  # noqa: BLE001 - no Energy dashboard
            return
        ids: dict[str, set[str]] = {"grid_in": set(), "grid_out": set(), "solar": set()}
        for s in sources:
            if s.get("type") == "grid":
                for f in s.get("flow_from") or []:
                    if f.get("stat_energy_from"):
                        ids["grid_in"].add(f["stat_energy_from"])
                for f in s.get("flow_to") or []:
                    if f.get("stat_energy_to"):
                        ids["grid_out"].add(f["stat_energy_to"])
                if s.get("stat_energy_from"):
                    ids["grid_in"].add(s["stat_energy_from"])
                if s.get("stat_energy_to"):
                    ids["grid_out"].add(s["stat_energy_to"])
            elif s.get("type") == "solar" and s.get("stat_energy_from"):
                ids["solar"].add(s["stat_energy_from"])
        every = set().union(*ids.values())
        if not ids["grid_in"]:
            return
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            from homeassistant.components.recorder import get_instance  # noqa: PLC0415
            from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415

            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period, self.hass, dt_util.as_utc(start), dt_util.as_utc(now), every, "hour", None, {"change"})
        except Exception:  # noqa: BLE001
            return
        per: dict[str, list[float]] = {k: [0.0] * 24 for k in ids}
        seen: set[int] = set()
        for sid, rows in stats.items():
            kinds = [k for k, v in ids.items() if sid in v]
            for r in rows:
                if r.get("change") is None:
                    continue
                t = dt_util.utc_from_timestamp(r["start"]) if isinstance(r["start"], (int, float)) else r["start"]
                lt = dt_util.as_local(t)
                if lt.date() != start.date():
                    continue
                seen.add(lt.hour)
                for k in kinds:
                    per[k][lt.hour] += max(0.0, r["change"])
        self.fill_hours(key, per, seen, now.hour)

    def fill_hours(self, key: str, per: dict[str, list[float]], seen: set[int], hour_now: int) -> None:
        """Put statistics into the past hours RoomControl did not count."""
        day = self.days.setdefault(key, {"rooms": {}, "rooms_cost": {}})
        hrs = day.setdefault("hours", {})
        for k in HOUR_KEYS:
            if not isinstance(hrs.get(k), list) or len(hrs[k]) != 24:
                hrs[k] = [0.0] * 24
        filled = set(day.get("filled") or [])
        for h in sorted(seen):
            if h >= hour_now or hrs["house"][h] > 0.001 or hrs["grid_in"][h] > 0.001:
                continue
            gi, go, so = per.get("grid_in", [0.0] * 24)[h], per.get("grid_out", [0.0] * 24)[h], per.get("solar", [0.0] * 24)[h]
            hrs["grid_in"][h], hrs["grid_out"][h], hrs["solar"][h] = round(gi, 5), round(go, 5), round(so, 5)
            hrs["house"][h] = round(max(0.0, gi + so - go), 5)
            filled.add(h)
        if filled:
            day["filled"] = sorted(filled)
            self._save()

    def _per_outdoor(self, day: dict[str, Any], hours: float, buy: float | None, status: dict[str, Any]) -> None:
        """The air conditioners' outdoor units (measured or estimated, energy.py
        status "outdoor"), split over their running indoor units; while
        heating that is heat ("heat") for the gas comparison."""
        from .heating import device_room  # noqa: PLC0415

        for unit in status.get("outdoor") or []:
            for c, w in (unit.get("split") or {}).items():
                kwh = w / 1000 * hours
                key = f"{device_room(self.hass, c) or ''}|ac:{c}"
                rec = day.setdefault("ac", {}).setdefault(key, {"kwh": 0.0, "eur": 0.0, "heat": 0.0, "heat_eur": 0.0})
                rec["kwh"] = round(rec["kwh"] + kwh, 5)
                eur = kwh * buy if buy is not None else 0.0
                rec["eur"] = round(rec["eur"] + eur, 5)
                if (unit.get("heating") or {}).get(c):
                    rec["heat"] = round(rec["heat"] + kwh, 5)
                    rec["heat_eur"] = round(rec["heat_eur"] + eur, 5)

    def device_today(self, area: str | None, climate: str) -> dict[str, Any] | None:
        rec = (self.days.get(dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m-%d")) or {}).get("ac", {}).get(f"{area or ''}|ac:{climate}")
        return None if rec is None else {k: round(v, 3) for k, v in rec.items()}

    def use_profile(self, days: int = 7) -> dict[str, Any] | None:
        """The house's expected use per local hour: the median kWh of that hour
        over the last `days` full days that have hours (Energy › Planning)."""
        import statistics  # noqa: PLC0415

        today = dt_util.as_local(dt_util.utcnow()).date()
        cols: list[list[float]] = [[] for _ in range(24)]
        used = 0
        for i in range(1, days + 1):
            h = ((self.days.get((today - timedelta(days=i)).isoformat()) or {}).get("hours") or {}).get("house")
            if not isinstance(h, list) or len(h) != 24 or sum(h) < 0.5:
                continue
            used += 1
            for k, v in enumerate(h):
                cols[k].append(float(v))
        if not used:
            return None
        return {"kw": [round(statistics.median(c), 2) if c else 0.0 for c in cols], "days": used}

    def heat_totals(self, area: str | None) -> dict[str, dict[str, Any]]:
        """Heaters' kWh and € today, the last 7 days and this month (one room, or all)."""
        now = dt_util.as_local(dt_util.utcnow())
        today = now.strftime("%Y-%m-%d")
        week = {(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)}
        month = now.strftime("%Y-%m")
        out = {k: {"kwh": 0.0, "eur": 0.0, "kwh_hp": 0.0, "eur_hp": 0.0} for k in ("day", "week", "month")}
        for key, day in self.days.items():
            if not (key == today or key in week or key.startswith(month)):
                continue
            for pk, rec in (day.get("heat") or {}).items():
                if area is not None and not pk.startswith(f"{area}|"):
                    continue
                for period, hit in (("day", key == today), ("week", key in week), ("month", key.startswith(month))):
                    if hit:
                        out[period]["kwh"] += rec.get("kwh", 0.0)
                        out[period]["eur"] += rec.get("eur", 0.0)
            for pk, rec in (day.get("ac") or {}).items():
                if area is not None and not pk.startswith(f"{area}|"):
                    continue
                for period, hit in (("day", key == today), ("week", key in week), ("month", key.startswith(month))):
                    if hit:
                        out[period]["kwh_hp"] += rec.get("heat", 0.0)
                        out[period]["eur_hp"] += rec.get("heat_eur", 0.0)
        return {k: {x: round(y, 3) for x, y in v.items()} for k, v in out.items()}

    def overview2(self) -> dict[str, Any]:
        """Energy → Overzicht 2: the hours of today, yesterday, the parts and the tips."""
        now = dt_util.as_local(dt_util.utcnow())
        key = now.strftime("%Y-%m-%d")
        yest = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        today = self.days.get(key) or {}
        ydays = self.days.get(yest) or {}
        hrs = today.get("hours") or {}
        hours = {k: [round(v, 3) for v in (hrs.get(k) or [0.0] * 24)] for k in HOUR_KEYS}
        names = today.get("names") or {}
        parts = []
        for pk, rec in (today.get("parts") or {}).items():
            if rec.get("kwh", 0.0) < 0.005 and rec.get("min", 0.0) < 1:
                continue
            area, part = pk.split("|", 1)
            parts.append({"area": area, "key": part, "kind": part.split(":", 1)[0], "name": names.get(pk, part),
                          "kwh": round(rec.get("kwh", 0.0), 3), "min": round(rec.get("min", 0.0)), "n": int(rec.get("n", 0))})
        parts.sort(key=lambda x: -x["kwh"])
        y_upto = None
        yh = (ydays.get("hours") or {}).get("house")
        if isinstance(yh, list) and len(yh) == 24:
            y_upto = round(sum(yh[: now.hour]) + yh[now.hour] * now.minute / 60, 2)
        try:
            tips = self.coach().get("tips") or []
        except Exception:  # noqa: BLE001 - tips are a bonus
            tips = []
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        status = (getattr(energy, "last_status", None) or (energy.status() if energy else {})) or {}
        live = []
        for area, r in (status.get("rooms") or {}).items():
            for p in r.get("parts") or []:
                if p.get("kind") in ("bundle", "switch", "meter", "ac") and (p.get("watts") or 0) >= 1:
                    live.append({"area": area, "key": p["key"], "kind": p["kind"], "name": p.get("name") or p["key"],
                                 "watts": round(p["watts"], 1)})
        car = status.get("car") or {}
        if car.get("charging") and car.get("kw"):
            live.append({"area": None, "key": "car", "kind": "car", "name": car.get("name") or None, "watts": round(car["kw"] * 1000)})
        live.sort(key=lambda x: -x["watts"])
        return {"hour": now.hour, "minute": now.minute, "hours": hours, "filled": today.get("filled") or [], "live": live[:6],
                "yesterday": {"house": round(ydays.get("house", 0.0), 2) if ydays else None, "house_upto": y_upto},
                "parts": parts[:12], "tips": tips[:4]}

    def _room(self, area: str) -> dict[str, Any]:
        return next((r for r in self.hass.data.get(DOMAIN, {}).get("rooms", []) if r.get("area_id") == area), {})

    def _bundle_lamps(self, area: str, part: str) -> set[str]:
        gid = part.split(":", 1)[1] if part.startswith("bundle:") else None
        for g in self._room(area).get("groups") or []:
            if gid is not None and str(g.get("id")) == gid:
                return set(g.get("lights") or [])
        return set()

    # ── the coach ──────────────────────────────────────────────────────────

    def _week(self, offset: int = 0) -> list[str]:
        """Local dates of this week (Monday to today), `offset` weeks back (same number of days)."""
        today = dt_util.as_local(dt_util.utcnow()).date()
        monday = today - timedelta(days=today.weekday())
        return [(monday - timedelta(weeks=offset) + timedelta(days=i)).isoformat() for i in range(today.weekday() + 1)]

    def coach(self) -> dict[str, Any]:
        from .room_switches import room_switches  # noqa: PLC0415

        week, prev = self._week(), self._week(1)
        n_days = len(week)
        scale = 7 / n_days

        def cost(days: list[str]) -> float | None:
            rows = [self.days[d] for d in days if "cost_in" in self.days.get(d, {})]
            return round(sum(r.get("cost_in", 0.0) - r.get("earn_out", 0.0) for r in rows), 2) if rows else None

        def merged(kind: str) -> dict[str, dict[str, float]]:
            out: dict[str, dict[str, float]] = {}
            for d in week:
                for key, rec in (self.days.get(d, {}).get(kind) or {}).items():
                    o = out.setdefault(key, {})
                    for k, v in rec.items():
                        if k == "w":
                            o["w"] = max(o.get("w", 0.0), v)
                        else:
                            o[k] = o.get(k, 0.0) + v
            return out

        names: dict[str, str] = {}
        for d in week:
            names.update(self.days.get(d, {}).get("names") or {})
        idle, away = merged("idle"), merged("away")
        tips: list[dict[str, Any]] = []
        for key, rec in idle.items():
            if rec.get("n", 0) < 3 and rec.get("eur", 0.0) < 0.1:
                continue
            area, part = key.split("|", 1)
            gid = part.split(":", 1)[1] if part.startswith("bundle:") else None
            group = next((g for g in self._room(area).get("groups") or [] if str(g.get("id")) == gid), None)
            can = group is not None and not group.get("idle_off")
            tips.append({"id": f"idle|{key}", "kind": "idle", "area": area, "name": names.get(key, part),
                         "n": int(rec.get("n", 0)), "kwh": round(rec["kwh"], 2), "per_week": round(rec["eur"] * scale, 2),
                         "on_motion": bool(group.get("on_motion", True)) if group else None,
                         "apply": {"type": "bundle_idle_off", "area": area, "group": gid} if can else None})
        switches = {sw["entity_id"]: sw for r in self.hass.data.get(DOMAIN, {}).get("rooms", []) for sw in room_switches(r)}
        for key, rec in away.items():
            if rec.get("h", 0.0) < 10 or rec.get("eur", 0.0) < 0.05:
                continue
            area, part = key.split("|", 1)
            entity = part.split(":", 1)[1] if part.startswith("switch:") else None
            sw = switches.get(entity) if entity else None
            can = entity is not None and (sw is None or ("nobody_home" not in sw["off_on"] and sw["may_off"]))
            tips.append({"id": f"away|{key}", "kind": "away", "area": area, "name": names.get(key, part),
                         "h": round(rec["h"], 1), "w": round(rec.get("w", 0.0)), "per_week": round(rec["eur"] * scale, 2),
                         "apply": {"type": "switch_nobody_home", "area": area, "entity": entity} if can else None})
        tips += self._task_tips(week, scale)
        house = sum(self.days.get(d, {}).get("house", 0.0) for d in week)
        unassigned = sum(self.days.get(d, {}).get("unassigned", 0.0) for d in week)
        if house > 5 and unassigned / house > 0.3:
            tips.append({"id": "unassigned", "kind": "unassigned", "pct": round(unassigned / house * 100), "per_week": None, "apply": None})
        tips = [t for t in tips if t["id"] not in self.dismissed]
        tips.sort(key=lambda t: -(t.get("per_week") or 0))
        # What went well
        planner = self.hass.data.get(DOMAIN, {}).get("planner")
        runs = [r for r in (getattr(planner, "runs", None) or []) if dt_util.as_local(dt_util.parse_datetime(r["at"])).date().isoformat() in week]
        saved_plan = sum((r.get("ref") or 0) - (r.get("cost") or 0) for r in runs if r.get("ref") is not None and r.get("cost") is not None)
        grace = 0
        for light in self.hass.data.get(DOMAIN, {}).get("entities", {}).values():
            for e in list(getattr(getattr(light, "_debug", None), "entries", []) or []):
                if e.get("kind") == "off" and e.get("reason") == "no_motion" and dt_util.as_local(dt_util.parse_datetime(e["at"])).date().isoformat() in week:
                    grace += 1
        good = []
        car_runs = [r for r in runs if r.get("key") == "car"]
        if car_runs:
            good.append({"kind": "car", "n": len(car_runs)})
        if grace:
            good.append({"kind": "grace", "n": grace})
        if runs and saved_plan > 0:
            good.append({"kind": "plan", "eur": round(saved_plan, 2), "n": len(runs)})
        # Cost per room this week
        per_room: dict[str, float] = {}
        house_cost = 0.0
        for d in week:
            day = self.days.get(d, {})
            for area, eur in (day.get("rooms_cost") or {}).items():
                per_room[area] = per_room.get(area, 0.0) + eur
            house_cost += day.get("house_cost", 0.0)
        avg = house_cost / house if house else None
        rooms = [{"area": a, "eur": round(v, 2)} for a, v in sorted(per_room.items(), key=lambda kv: -kv[1])]
        if avg is not None and unassigned:
            rooms.append({"area": None, "eur": round(unassigned * avg, 2)})
        wasted = sum(r.get("eur", 0.0) for r in idle.values()) + sum(r.get("eur", 0.0) for r in away.values())
        today = dt_util.as_local(dt_util.utcnow()).date()
        return {"week": today.isocalendar()[1], "days": n_days, "cost": cost(week), "cost_prev": cost(prev),
                "wasted": round(wasted, 2), "saved": round(saved_plan, 2) if runs else None,
                "tips_total": round(sum(t.get("per_week") or 0 for t in tips), 2),
                "tips": tips[:6], "good": good, "rooms": rooms, "dismissed": len(self.dismissed)}

    def _task_tips(self, week: list[str], scale: float) -> list[dict[str, Any]]:
        """Programs started at a dear hour: what the cheapest hour of that day would have saved."""
        from .offpay import hour_key  # noqa: PLC0415

        offpay = self.hass.data.get(DOMAIN, {}).get("offpay")
        if offpay is None:
            return []
        prices: dict[str, float] = getattr(offpay, "prices", {}) or {}
        out = []
        for key, entity in offpay.switches().items():
            kind, _g = offpay.kind(key)
            if kind != "task":
                continue
            learner = offpay.learning.learners.get(key)
            saved, n, hours = 0.0, 0, []
            for c in (learner.data.get("cycles") or []) if learner else []:
                start = dt_util.parse_datetime(c["start"])
                if start is None:
                    continue
                local = dt_util.as_local(start)
                if local.date().isoformat() not in week:
                    continue
                day = [prices.get(f"{local.strftime('%Y-%m-%d')}T{h:02d}") for h in range(24)]
                known = [(h, p) for h, p in enumerate(day) if p is not None]
                at = prices.get(hour_key(start))
                if not known or at is None:
                    continue
                best_h, best_p = min(known, key=lambda x: x[1])
                if at - best_p > 0.05:
                    saved += (at - best_p) * c["kwh"]
                    n += 1
                    hours.append(best_h)
            if n >= 2 and saved >= 0.1:
                usual = max(set(hours), key=hours.count)
                out.append({"id": f"task|{key}", "kind": "task", "area": key.split("|", 1)[0],
                            "name": offpay.learning.names.get(key, entity), "n": n, "best": f"{usual:02d}:00",
                            "per_week": round(saved * scale, 2), "apply": None})
        return out

    async def async_apply(self, tip_id: str) -> bool:
        """Apply a tip's setting (a light bundle off after the grace period, a
        switch off when nobody is home)."""
        from . import _async_save  # noqa: PLC0415

        tip = next((t for t in self.coach()["tips"] if t["id"] == tip_id), None)
        act = (tip or {}).get("apply")
        if not act:
            return False
        rooms = [dict(r) for r in self.hass.data.get(DOMAIN, {}).get("rooms", [])]
        for i, room in enumerate(rooms):
            if room.get("area_id") != act["area"]:
                continue
            if act["type"] == "bundle_idle_off":
                room["groups"] = [{**g, "idle_off": True} if str(g.get("id")) == act["group"] else g for g in room.get("groups") or []]
            elif act["type"] == "switch_nobody_home":
                sws = [dict(sw) for sw in room.get("switches") or []]
                for sw in sws:
                    if sw.get("entity_id") == act["entity"]:
                        off_on = sw.get("off_on") if isinstance(sw.get("off_on"), list) else ["all_off", "nobody_home", "smoke"]
                        sw["off_on"] = list(dict.fromkeys([*off_on, "nobody_home"]))
                        sw["back_on"] = True
                        break
                else:
                    sws.append({"entity_id": act["entity"], "off_on": ["all_off", "nobody_home", "smoke"], "back_on": True})
                room["switches"] = sws
            rooms[i] = room
            await _async_save(self.hass, rooms=rooms)
            return True
        return False

    def dismiss(self, tip_id: str) -> None:
        if tip_id not in self.dismissed:
            self.dismissed.append(tip_id)
            self._save()

    # ── for the panel ──────────────────────────────────────────────────────

    def base_load(self) -> dict[str, Any] | None:
        """The last 7 nights: the house's average power and the parts that stay on."""
        today = dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m-%d")
        nights = [v for k, v in sorted(self.nights.items()) if v.get("n", 0) >= 20 and k <= today][-7:]
        if not nights:
            return None
        house = sum(v["house"] for v in nights) / len(nights)
        parts: dict[str, list[float]] = {}
        names: dict[str, str] = {}
        for v in nights:
            for k, w in (v.get("parts") or {}).items():
                parts.setdefault(k, []).append(w)
                names[k] = (v.get("names") or {}).get(k, k)
        avg = {k: sum(ws) / len(ws) for k, ws in parts.items()}
        known = [{"key": k, "area": k.split("|", 1)[0], "name": names[k], "watts": round(w, 1)}
                 for k, w in sorted(avg.items(), key=lambda kv: -kv[1]) if w >= 1]
        known_w = sum(p["watts"] for p in known)
        return {"watts": round(house, 1), "nights": len(nights), "parts": known[:8],
                "unassigned": round(max(0.0, house - known_w), 1)}

    def overview(self) -> dict[str, Any]:
        from .tariff import buy_now  # noqa: PLC0415

        hass = self.hass
        cfg = _cfg(hass)
        energy = hass.data.get(DOMAIN, {}).get("energy")
        status = (getattr(energy, "last_status", None) or (energy.status() if energy else {})) or {}
        detail = status.get("phase_detail") or {}
        phases = status.get("phases") or {}
        rooms = status.get("rooms") or {}
        car = status.get("car") or {}
        used = [d.get("consumed") for d in detail.values()]
        grid_w = None
        if used and all(u is not None for u in used):
            grid_w = sum(used) - sum(d.get("produced") or 0 for d in detail.values())
        solar_vals = [d.get("solar") for d in detail.values() if d.get("solar") is not None]
        house_vals = [v for v in phases.values() if v is not None]
        house_w = sum(house_vals) if house_vals and len(house_vals) == len(phases) else None
        car_w = (car.get("kw") or 0.0) * 1000 if car.get("charging") else 0.0
        rooms_w = sum((r.get("watts") or 0.0) for r in rooms.values())
        today = self.days.get(dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m-%d")) or {}
        fuse = float(cfg.get("fuse_a") or DEFAULT_FUSE)
        phase_rows = []
        for p, d in detail.items():
            amps = max(d.get("consumed") or 0.0, d.get("produced") or 0.0) / VOLT
            phase_rows.append({"phase": p, "amps": round(amps, 1),
                               "rooms": [a for a, r in rooms.items() if (r.get("phase") or "L1") == p]})
        warning = None
        if car and not car.get("charging") and detail:
            cp = car.get("phase") or "L1"
            row = next((r for r in phase_rows if r["phase"] == cp), None)
            add = float(cfg.get("charger_max_kw") or 3.7) * 1000 / VOLT
            if row and row["amps"] + add > fuse:
                warning = {"phase": cp, "car_a": round(add), "total_a": round(row["amps"] + add)}
        room_rows = []
        for area, r in rooms.items():
            parts = sorted([p for p in r.get("parts") or [] if (p.get("watts") or 0) >= 1], key=lambda p: -(p.get("watts") or 0))
            room_rows.append({"area": area, "watts": r.get("watts") or 0.0,
                              "top": [{"name": p.get("name") or p["key"], "watts": p["watts"]} for p in parts[:3]],
                              "kwh": round((today.get("rooms") or {}).get(area, 0.0), 2),
                              "cost": round((today.get("rooms_cost") or {}).get(area, 0.0), 2) if today.get("rooms_cost") else None})
        room_rows.sort(key=lambda r: (-r["watts"], -r["kwh"]))
        base = self.base_load()
        price = buy_now(hass)
        if base and price is not None:
            base["month"] = round(base["watts"] / 1000 * 24 * 30 * price, 2)
        return {
            "configured": bool(status.get("configured")),
            "price": price,
            "now": {"grid_w": None if grid_w is None else round(grid_w), "solar_w": round(sum(solar_vals)) if solar_vals else None,
                    "house_w": None if house_w is None else round(house_w), "car_w": round(car_w),
                    "rooms_w": round(rooms_w), "unassigned_w": None if house_w is None else round(max(0.0, house_w - rooms_w - car_w)),
                    "car": {"charging": bool(car.get("charging")), "name": car.get("name") or None} if car else None},
            "today": {k: round(today.get(k, 0.0), 2) for k in ("house", "grid_in", "grid_out", "solar", "car", "unassigned",
                                                                  "cost_in", "earn_out", "house_cost") if k in today},
            "has_solar": bool(cfg.get("has_solar")),
            "fuse_a": fuse, "phases": phase_rows, "warning": warning,
            "rooms": room_rows, "base": base,
            "upcoming": self._upcoming(), "recent": self._recent(),
        }

    # ── the bill ───────────────────────────────────────────────────────────

    async def _gas_days(self, start: datetime, end: datetime) -> tuple[dict[str, float], bool]:
        """m³ per local day from the Energy dashboard's gas meter(s), and whether there is one."""
        try:
            from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

            manager = await async_get_manager(self.hass)
            ids = {s["stat_energy_from"] for s in (manager.data or {}).get("energy_sources") or []
                   if s.get("type") == "gas" and s.get("stat_energy_from")}
        except Exception:  # noqa: BLE001 - no Energy dashboard
            return {}, False
        if not ids:
            return {}, False
        try:
            from homeassistant.components.recorder import get_instance  # noqa: PLC0415
            from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415

            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period, self.hass, start, end, ids, "hour", None, {"change"})
        except Exception:  # noqa: BLE001
            return {}, True
        out: dict[str, float] = {}
        for rows in stats.values():
            for r in rows:
                if r.get("change") is None:
                    continue
                t = dt_util.utc_from_timestamp(r["start"]) if isinstance(r["start"], (int, float)) else r["start"]
                key = dt_util.as_local(t).strftime("%Y-%m-%d")
                out[key] = round(out.get(key, 0.0) + max(0.0, r["change"]), 4)
        return out, True

    async def async_bill(self, month: str | None = None) -> dict[str, Any]:
        """One month (YYYY-MM, default this one): per day electricity, gas and
        fixed costs, the total so far, the forecast and the advance payment."""
        cfg = _cfg(self.hass).get("bill") or {}
        now = dt_util.as_local(dt_util.utcnow())
        this_month = now.strftime("%Y-%m")
        month = month or this_month
        year, mon = (int(x) for x in month.split("-"))
        days_in = calendar.monthrange(year, mon)[1]
        first = now.replace(year=year, month=mon, day=1, hour=0, minute=0, second=0, microsecond=0)
        current = month == this_month
        upto = now.day if current else days_in
        termijn = cfg.get("termijn") if isinstance(cfg.get("termijn"), (int, float)) else None
        fixed = float(cfg.get("fixed_month") or 0.0)
        gas_price = cfg.get("gas_price") if isinstance(cfg.get("gas_price"), (int, float)) else None
        gas_from = first - timedelta(days=14) if current else first
        gas, has_gas = await self._gas_days(dt_util.as_utc(gas_from), dt_util.as_utc(first + timedelta(days=days_in)))
        rows = []
        for d in range(1, days_in + 1):
            key = f"{month}-{d:02d}"
            day = self.days.get(key) or {}
            elec = None if "cost_in" not in day else round(day.get("cost_in", 0.0) - day.get("earn_out", 0.0), 3)
            m3 = gas.get(key)
            rows.append({"day": d, "elec": elec, "kwh_in": round(day.get("grid_in", 0.0), 2) if day else None,
                         "kwh_out": round(day.get("grid_out", 0.0), 2) if day else None,
                         "gas_m3": m3, "gas": None if m3 is None or gas_price is None else round(m3 * gas_price, 3),
                         "fixed": round(fixed / days_in, 3), "future": current and d > upto})
        past = [r for r in rows if not r["future"]]
        elec_so_far = round(sum(r["elec"] or 0.0 for r in past), 2)
        gas_so_far = round(sum(r["gas"] or 0.0 for r in past), 2) if gas_price is not None and has_gas else None
        fixed_so_far = round(fixed / days_in * upto, 2)
        total = round(elec_so_far + (gas_so_far or 0.0) + fixed_so_far, 2)
        measured = [k for k, v in sorted(self.days.items()) if "cost_in" in v]
        out: dict[str, Any] = {
            "month": month, "current": current, "days": days_in, "upto": upto, "rows": rows,
            "elec": elec_so_far, "gas": gas_so_far, "fixed": fixed_so_far, "total": total,
            "kwh_in": round(sum(r["kwh_in"] or 0 for r in past), 1), "kwh_out": round(sum(r["kwh_out"] or 0 for r in past), 1),
            "gas_m3": round(sum(r["gas_m3"] or 0 for r in past), 2) if has_gas else None,
            "has_gas": has_gas, "gas_price": gas_price, "termijn": termijn, "fixed_month": fixed,
            "since": measured[0] if measured else None,
            "months": sorted({k[:7] for k in self.days} | {this_month}),
        }
        if current:
            # The average day of the last 14 days (electricity + gas), for the days to come.
            last = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 15)]
            elec_days = [self.days[k].get("cost_in", 0.0) - self.days[k].get("earn_out", 0.0) for k in last if "cost_in" in self.days.get(k, {})]
            gas_days = [gas[k] * gas_price for k in last if k in gas and gas_price is not None]
            per_day = (sum(elec_days) / len(elec_days) if elec_days else 0.0) + (sum(gas_days) / len(gas_days) if gas_days else 0.0)
            left = days_in - upto
            # today is only partly gone: count what is left of it too
            frac = 1 - (now.hour * 60 + now.minute) / 1440
            out["forecast"] = round(total + per_day * (left + frac) + fixed / days_in * left, 2) if elec_days else None
            out["per_day"] = round(per_day, 2) if elec_days else None
            if out["forecast"] is not None and termijn is not None:
                out["diff"] = round(out["forecast"] - termijn, 2)
        elif termijn is not None:
            out["diff"] = round(total - termijn, 2)
        return out

    def _upcoming(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        now = dt_util.utcnow()
        planner = self.hass.data.get(DOMAIN, {}).get("planner")
        for plan in (getattr(planner, "plans", None) or {}).values():
            block = plan.get("block")
            if not block or plan.get("done") or plan.get("mode_used") == "direct":
                continue
            start = dt_util.parse_datetime(block["start"])
            if start is None or start < now - timedelta(hours=1):
                continue
            dev = plan.get("device") or {}
            out.append({"at": block["start"], "end": block["end"], "kind": "plan", "device": dev.get("kind"),
                        "name": dev.get("name"), "mode": plan.get("mode_used"), "price": block.get("avg"),
                        "ready": plan.get("ready")})
        battery = self.hass.data.get(DOMAIN, {}).get("battery")
        if battery is not None and getattr(battery, "plan", None):
            for b in battery.blocks():
                if b["action"] in ("charge", "discharge") and dt_util.parse_datetime(b["end"]) > now:
                    out.append({"at": b["start"], "end": b["end"], "kind": "battery", "action": b["action"], "price": b.get("price")})
        out.sort(key=lambda x: x["at"])
        return out[:6]

    def _recent(self) -> list[dict[str, Any]]:
        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        rows = []
        for area, light in entities.items():
            buf = getattr(light, "_debug", None)
            for e in (list(getattr(buf, "entries", []) or [])[-40:]):
                if e.get("kind") in ("on", "off") and (e.get("reason", "").startswith(("plan_", "switches_")) or e.get("reason") in (
                        "nobody_home", "alarm armed away", "replay", "usage_schedule")):
                    rows.append({**{k: e.get(k) for k in ("at", "kind", "reason", "bundles")}, "area": area})
        rows.sort(key=lambda r: r["at"], reverse=True)
        return rows[:6]
