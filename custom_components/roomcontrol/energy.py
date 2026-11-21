"""Power per room and a "dumb" EV charger: is the car charging?

General setting "energy":
{"phases": 1 | 3,
 "phase_sensors": {"L1": sensor, "L2": sensor, "L3": sensor},  # consumed power per phase (W or kW)
 "has_solar": bool, "has_battery": bool,
 "produced_sensors": {"L1": sensor, ...},  # with solar or battery: power returned per phase
 "solar_sensors": {"L1": sensor, ...},  # optional: solar output per phase
 (older: "solar_sensor" + "solar_phase": "all" | "L1" | "L2" | "L3")
 "battery_sensor": sensor (+ discharging, − charging), "battery_phase": "all" | "L1"…,  # optional
 "charger_room": area id, "charger_phase": "L1" | "L2" | "L3",
 "charge_from_kw": 1.2,          # above this the car counts as charging
 "charger_max_kw": 3.7,
 "car_name": "Audi A3", "battery_kwh": 8.8,
 "soc_sensor": sensor (%), "charging_sensor": entity, "plug_sensor": entity,  # optional
 "price_kwh": 0.25,              # fixed price per kWh (without a price sensor)
 "history_days": 365}            # how long charging sessions are kept (0: forever)

Charging sessions (Store "roomcontrol.ev_sessions"): [{"start", "end", "kwh"
(the charger's use, the estimate added up), "grid_kwh" / "solar_kwh" (the
part from the grid / from your own solar panels and home battery: while the
house as a whole returns power, the car runs on its own power; else the
grid part is at most what the house takes from the grid), "battery_kwh"
(into the battery: the rise of the battery level × its size, when known),
"cost" (€, the grid part at the price of each moment; own power is free;
older sessions: all kWh), "saved" (€, the sun part at the price of each
moment: what it would have cost from the grid), "soc_from", "soc_to"}].

Room options: "phase": "L1" | "L2" | "L3" (3 phases only) and
"power": {"bundle:<group id>" | "switch:<entity>": {"sensor": entity} | {"watts": n}};
a light bundle may instead have one sensor per lamp: {"sensors": {lamp: sensor}}.
Energy (kWh) sensors per lamp / switch: {"energy": {entity: sensor | "none"}}
(without a choice: the kWh sensor on the same device); kept for later use.

A light bundle counts its watts times the brightness of its lamps that are
on; a switch its watts when on; a power sensor counts as it is.
The house's use on a phase = consumed − returned (+ the solar panels' and the
home battery's output on that phase, when their sensors are set; "all"
spreads them evenly over the phases). The car ≈ the use on the charger's
phase − the rooms on that phase.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.const import STATE_ON
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_GROUPS, DOMAIN
from .ev import EvNotifier, price_now, price_status
from .rooms import managed_areas

SETTING_ENERGY = "energy"
SIGNAL_ENERGY = "roomcontrol_energy"  # sent after each check (every 30 s)
PHASES = ("L1", "L2", "L3")
CHARGE_EFFICIENCY = 0.9  # of the power drawn, this much ends up in the battery
CHARGING_STATES = {"charging", "on", "true", "laden", "bezig met laden"}


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ENERGY) or {}


def _watts(hass: HomeAssistant, entity: str | None) -> float | None:
    """A power sensor in W (kW converted); None when unknown."""
    st = hass.states.get(entity) if entity else None
    if st is None:
        return None
    try:
        value = float(st.state)
    except (TypeError, ValueError):
        return None
    unit = str(st.attributes.get("unit_of_measurement") or "W").lower()
    return value * 1000 if unit == "kw" else value / 1000 if unit == "mw" else value


def _num(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@callback
def auto_sensor(hass: HomeAssistant, entity_id: str, unit: str = "w") -> str | None:
    """A sensor in this unit ("w": power, "kwh": energy) on the same device
    as this lamp or switch, if any."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    if entry is None or not entry.device_id:
        return None
    units = (unit,)  # W only (the user chose that), kWh only
    words = ("power", "vermogen", "verbruik") if unit == "w" else ("energy", "energie", "total", "totaal")
    found: list[tuple[tuple[int, int, int], str]] = []
    for other in er.async_entries_for_device(ent_reg, entry.device_id):
        if other.domain != "sensor" or other.disabled_by:
            continue
        st = hass.states.get(other.entity_id)
        have = str((st.attributes.get("unit_of_measurement") if st else None) or other.unit_of_measurement or "").lower()
        if have not in units:
            continue
        try:
            numeric = st is not None and float(st.state) == float(st.state)
        except (TypeError, ValueError):
            numeric = False
        name = f"{other.entity_id} {other.original_name or ''} {other.name or ''}".lower()
        # Best first: a value now, then the right kind, then a fitting name.
        rank = (0 if numeric else 1,
                0 if (st.attributes.get("device_class") if st else other.original_device_class) in ("power", "energy") else 1,
                0 if any(w in name for w in words) else 1)
        found.append((rank, other.entity_id))
    return sorted(found)[0][1] if found else None


@callback
def auto_power_sensor(hass: HomeAssistant, entity_id: str) -> str | None:
    """The power sensor (W) on the same device as this lamp or switch."""
    return auto_sensor(hass, entity_id, "w")


@callback
def energy_sensors(hass: HomeAssistant, conf: dict[str, Any], entities: list[str]) -> dict[str, str]:
    """The energy (kWh) sensor per lamp / switch: chosen ("energy": {entity:
    sensor | "none"}), else matched on the same device. Kept for features
    that count consumption over time."""
    chosen = conf.get("energy") or {}
    out: dict[str, str] = {}
    for entity in entities:
        pick = chosen.get(entity)
        if pick == "none":
            continue
        if pick or (pick := auto_sensor(hass, entity, "kwh")):
            out[entity] = pick
    return out


def _kwh(hass: HomeAssistant, entity: str | None) -> float | None:
    st = hass.states.get(entity) if entity else None
    try:
        value = float(st.state) if st is not None else None
    except (TypeError, ValueError):
        return None
    if value is None:
        return None
    unit = str(st.attributes.get("unit_of_measurement") or "kWh").lower()
    return value / 1000 if unit == "wh" else value


@callback
def room_parts(hass: HomeAssistant, room: dict[str, Any]) -> list[dict[str, Any]]:
    """Power of each light bundle and switch of the room: [{key, name, watts, source}].

    A part without a choice of its own uses the power sensor on the same
    device as its lamp / switch (matched automatically). A chosen sensor
    wins; "none" means: no sensor for this lamp / switch."""
    from .room_switches import room_switches  # here: avoids an import cycle

    power = room.get("power") or {}
    out: list[dict[str, Any]] = []
    for index, group in enumerate(room.get(CONF_GROUPS, []) or []):
        key = f"bundle:{group.get('id') or index}"
        conf = power.get(key) or {}
        lamps = [e for e in group.get("lights", []) or [] if e]
        fixed = "watts" in conf and conf.get("mode") != "sensor"
        chosen = conf.get("sensors") or {}
        per_lamp: dict[str, str] = {}
        auto = False
        if not fixed and not conf.get("sensor"):
            for lamp in lamps:
                pick = chosen.get(lamp)
                if pick == "none":
                    continue
                if not pick and (pick := auto_power_sensor(hass, lamp)):
                    auto = True
                if pick:
                    per_lamp[lamp] = pick
        if per_lamp:
            # One power sensor per lamp of the bundle: their sum.
            values = [w for w in (_watts(hass, x) for x in per_lamp.values()) if w is not None]
            watts, source = (sum(values) if values else None), "sensor"
        elif conf.get("sensor") and not fixed:
            watts, source = _watts(hass, conf["sensor"]), "sensor"
        else:
            on = [hass.states.get(e) for e in lamps]
            on = [s for s in on if s is not None and s.state == STATE_ON]
            level = (sum((s.attributes.get("brightness") or 255) for s in on) / (255 * len(on))) if on else 0
            watts, source = (_num(conf.get("watts"), 0) * level if on else 0.0), "watts"
        energy = energy_sensors(hass, conf, lamps)
        kwh = [v for v in (_kwh(hass, x) for x in energy.values()) if v is not None]
        out.append({"key": key, "kind": "bundle", "name": (group.get("name") or "").strip() or f"#{index + 1}",
                    "watts": watts, "source": source, "auto": auto, "sensors": per_lamp,
                    "energy": energy, "kwh": round(sum(kwh), 3) if kwh else None})
    for sw in room_switches(room):
        key = f"switch:{sw['entity_id']}"
        conf = power.get(key) or {}
        fixed = "watts" in conf and conf.get("mode") != "sensor"
        sensor = conf.get("sensor")
        auto = False
        if not fixed and not sensor:
            sensor = auto_power_sensor(hass, sw["entity_id"])
            auto = bool(sensor)
        if sensor and sensor != "none" and not fixed:
            watts, source = _watts(hass, sensor), "sensor"
        else:
            st = hass.states.get(sw["entity_id"])
            watts, source = (_num(conf.get("watts"), 0) if st is not None and st.state == STATE_ON else 0.0), "watts"
        st = hass.states.get(sw["entity_id"])
        energy = energy_sensors(hass, conf, [sw["entity_id"]])
        kwh = _kwh(hass, energy.get(sw["entity_id"]))
        out.append({"key": key, "kind": "switch",
                    "name": (st.attributes.get("friendly_name") if st else None) or sw["entity_id"],
                    "watts": watts, "source": source, "auto": auto,
                    "energy": energy, "kwh": None if kwh is None else round(kwh, 3)})
    out += room_meters(hass, room, out)
    return out


_MEASURE_WORDS = {
    "energie", "energy", "vermogen", "power", "verbruik", "consumption", "spanning", "voltage",
    "stroom", "current", "frequentie", "frequency", "totaal", "total", "huidig", "actueel",
    "w", "kw", "kwh", "a", "v", "hz",
}


def meter_name(names: list[str], device: str | None = None) -> str:
    """A name for a meter from its sensors' names: their common start, without
    measurement words ("Combi-oven energie" + "Combi-oven vermogen" →
    "Combi-oven"); else the device name; else the first sensor's name."""
    words = [str(n).split() for n in names if n]
    common: list[str] = []
    if words:
        for parts in zip(*words):
            if all(p.lower() == parts[0].lower() for p in parts):
                common.append(parts[0])
            else:
                break
    while common and common[-1].lower().strip(":-()") in _MEASURE_WORDS:
        common.pop()
    if not common and words:
        first = [w for w in words[0] if w.lower().strip(":-()") not in _MEASURE_WORDS]
        common = first if len(words) == 1 else []
    return " ".join(common) or device or (names[0] if names else "?")


@callback
def room_meters(hass: HomeAssistant, room: dict[str, Any], parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dummy switches: power (W) and energy (kWh) sensors in the room's area
    that belong to none of its lamps or switches, one per device (e.g. the
    meter of a washing machine). They count in the room's power.
    Room option "power": {"meter:<device id or sensor>": {"hidden": true} |
    {"sensor": W sensor | "none", "energy_sensor": kWh sensor | "none",
    "name": a name of the user's own}}. Without a name of its own the meter is
    named after its sensors (meter_name)."""
    from .room_switches import room_switches  # here: avoids an import cycle

    area = room.get("area_id")
    if not area:
        return []
    ent_reg, dev_reg = er.async_get(hass), dr.async_get(hass)
    taken_devices: set[str] = set()
    for entity in [e for g in room.get(CONF_GROUPS, []) or [] for e in g.get("lights", []) or []] + [
            sw["entity_id"] for sw in room_switches(room)]:
        entry = ent_reg.async_get(entity)
        if entry is not None and entry.device_id:
            taken_devices.add(entry.device_id)
    taken_sensors = {x for p in parts for x in [*(p.get("sensors") or {}).values(), *(p.get("energy") or {}).values()]}
    for conf in (room.get("power") or {}).values():
        taken_sensors |= {conf.get("sensor")} | set((conf.get("sensors") or {}).values()) | set((conf.get("energy") or {}).values())
    groups: dict[str, dict[str, Any]] = {}
    for entry in ent_reg.entities.values():
        if entry.domain != "sensor" or entry.disabled_by or entry.platform == DOMAIN:
            continue
        device = dev_reg.async_get(entry.device_id) if entry.device_id else None
        if (entry.area_id or (device.area_id if device else None)) != area:
            continue
        if entry.device_id in taken_devices or entry.entity_id in taken_sensors:
            continue
        st = hass.states.get(entry.entity_id)
        unit = str((st.attributes.get("unit_of_measurement") if st else None) or entry.unit_of_measurement or "").lower()
        if unit not in ("w", "kwh"):
            continue
        key = f"meter:{entry.device_id or entry.entity_id}"
        group = groups.setdefault(key, {"w": [], "kwh": [], "names": [],
                                        "device": (device.name_by_user or device.name) if device else None})
        group["w" if unit == "w" else "kwh"].append(entry.entity_id)
        group["names"].append((st.attributes.get("friendly_name") if st else None) or entry.original_name or entry.entity_id)
    power = room.get("power") or {}
    out = []
    for group in groups.values():
        group["name"] = meter_name(group["names"], group["device"])
    for key, group in sorted(groups.items(), key=lambda kv: str(kv[1]["name"]).lower()):
        conf = power.get(key) or {}
        w_sensor = conf.get("sensor") or (sorted(group["w"])[0] if group["w"] else None)
        e_sensor = conf.get("energy_sensor") or (sorted(group["kwh"])[0] if group["kwh"] else None)
        w_sensor = None if w_sensor == "none" else w_sensor
        e_sensor = None if e_sensor == "none" else e_sensor
        kwh = _kwh(hass, e_sensor)
        out.append({"key": key, "kind": "meter", "name": (conf.get("name") or "").strip() or group["name"],
                    "found_name": group["name"], "hidden": bool(conf.get("hidden")),
                    "watts": None if conf.get("hidden") else (_watts(hass, w_sensor) if w_sensor else 0.0),
                    "source": "sensor", "auto": not conf.get("sensor"), "sensor": w_sensor,
                    "energy_sensor": e_sensor, "kwh": None if kwh is None else round(kwh, 3),
                    "w_options": sorted(group["w"]), "kwh_options": sorted(group["kwh"])})
    return out


class Energy:
    """Keeps track of the car's charging: since when, how much and what it cost,
    and the past charging sessions."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsub: CALLBACK_TYPE | None = None
        self.charging_since: datetime | None = None
        self.charged_kwh = 0.0
        self.cost = 0.0
        self.grid_kwh = 0.0
        self.solar_kwh = 0.0
        self.saved = 0.0
        self.priced = False  # a price was known for (part of) this session
        self.soc_from: float | None = None
        self.soc_last: float | None = None
        # The car's battery level sensor (e.g. Audi Connect) updates only now
        # and then: what was charged since its last update, to estimate it.
        self.kwh_since_soc = 0.0
        self._soc_seen: tuple[str, str] | None = None
        self._last: datetime | None = None
        self.sessions: list[dict[str, Any]] = []
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.ev_sessions")
        self.notifier = EvNotifier(hass)
        self.sun: list[dict[str, Any]] = []  # solar forecast periods (solar_forecast.py)
        self._sun_at: datetime | None = None
        self._sun_for: tuple[str, ...] = ()

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.sessions = [s for s in data.get("sessions", []) if isinstance(s, dict)]
        cur = data.get("current")
        if isinstance(cur, dict) and (since := dt_util.parse_datetime(cur.get("since") or "")):
            # Charging when Home Assistant stopped: carry on with that session.
            self.charging_since = since
            self.charged_kwh = float(cur.get("kwh") or 0)
            self.cost = float(cur.get("cost") or 0)
            self.grid_kwh = float(cur.get("grid_kwh") or 0)
            self.solar_kwh = float(cur.get("solar_kwh") or 0)
            self.saved = float(cur.get("saved") or 0)
            self.priced = bool(cur.get("priced"))
            self.soc_from = cur.get("soc_from")
        self._prune()

    def _keep(self) -> None:
        def data() -> dict[str, Any]:
            cur = None
            if self.charging_since:
                cur = {"since": self.charging_since.isoformat(), "kwh": self.charged_kwh, "cost": self.cost,
                       "grid_kwh": self.grid_kwh, "solar_kwh": self.solar_kwh, "saved": self.saved,
                       "priced": self.priced, "soc_from": self.soc_from}
            return {"sessions": self.sessions, "current": cur}
        self._store.async_delay_save(data, 5)

    def _prune(self) -> None:
        days = _num(_cfg(self.hass).get("history_days"), 365)
        if days > 0:
            since = (dt_util.utcnow() - timedelta(days=days)).isoformat()
            self.sessions = [s for s in self.sessions if (s.get("end") or "") >= since]

    def price_kwh(self) -> float | None:
        """The price per kWh now: the price sensor, else the fixed price."""
        cfg = _cfg(self.hass)
        if cfg.get("price_sensor"):
            from .ev import price_forecast
            sensor = cfg["price_sensor"]
            if (p := price_now(self.hass, sensor, price_forecast(self.hass, sensor))) is not None:
                return p
        value = cfg.get("price_kwh")
        return float(value) if isinstance(value, (int, float)) else None

    @callback
    def start(self) -> None:
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(seconds=30))

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _end_session(self, now: datetime) -> None:
        if self.charging_since is None:
            return
        battery = _num(_cfg(self.hass).get("battery_kwh"), 8.8)
        added = None
        if self.soc_from is not None and self.soc_last is not None and self.soc_last >= self.soc_from:
            added = round((self.soc_last - self.soc_from) / 100 * battery, 2)
        if self.charged_kwh >= 0.05 or added:
            self.sessions.append({
                "start": self.charging_since.isoformat(), "end": now.isoformat(),
                "kwh": round(self.charged_kwh, 2), "battery_kwh": added,
                "cost": round(self.cost, 2) if self.priced else None,
                "grid_kwh": round(self.grid_kwh, 2), "solar_kwh": round(self.solar_kwh, 2),
                "saved": round(self.saved, 2) if self.priced else None,
                "soc_from": self.soc_from, "soc_to": self.soc_last,
            })
        self.charging_since, self._last = None, None
        self.charged_kwh, self.cost, self.priced = 0.0, 0.0, False
        self.grid_kwh = self.solar_kwh = self.saved = 0.0
        self.soc_from = None
        self._prune()
        self._keep()

    async def async_refresh_sun(self) -> None:
        from .solar_forecast import async_read, periods  # noqa: PLC0415

        ids = tuple(i for i in _cfg(self.hass).get("solar_forecast") or [] if isinstance(i, str))
        self._sun_for, self._sun_at = ids, dt_util.utcnow()
        self.sun = periods(await async_read(self.hass, list(ids))) if ids else []

    @callback
    def _tick(self, _now: Any = None) -> None:
        ids = tuple(i for i in _cfg(self.hass).get("solar_forecast") or [] if isinstance(i, str))
        if ids != self._sun_for or (ids and (self._sun_at is None or dt_util.utcnow() - self._sun_at > timedelta(minutes=15))):
            self._sun_for, self._sun_at = ids, dt_util.utcnow()
            self.hass.async_create_task(self.async_refresh_sun())
        cfg = _cfg(self.hass)
        new_reading = False
        if (st := self.hass.states.get(cfg.get("soc_sensor") or "")) is not None:
            seen = (st.state, st.last_updated.isoformat())
            if seen != self._soc_seen:
                self._soc_seen, new_reading = seen, True  # a new reading from the car
        status = self.status()
        car = status.get("car") or {}
        now = dt_util.utcnow()
        soc = car.get("soc")
        if car.get("charging"):
            if self.charging_since is None:
                self.charging_since, self.charged_kwh, self.cost, self.priced = now, 0.0, 0.0, False
                self.grid_kwh = self.solar_kwh = self.saved = 0.0
                self.soc_from = soc
            elif self._last is not None and car.get("kw"):
                hours = (now - self._last).total_seconds() / 3600
                kwh = car["kw"] * hours
                self.charged_kwh += kwh
                self.kwh_since_soc += kwh
                grid = self.grid_share(status, kwh, hours)
                self.grid_kwh += grid
                self.solar_kwh += kwh - grid
                if (price := self.price_kwh()) is not None:
                    self.cost += grid * price
                    self.saved += (kwh - grid) * price  # own power: what it would have cost
                    self.priced = True
            if self.soc_from is None:
                self.soc_from = soc
            if soc is not None:
                self.soc_last = soc
            self._last = now
            self._keep()
        else:
            if soc is not None:
                self.soc_last = soc
            self._end_session(now)
        if new_reading:
            # What was charged up to now is in the car's new reading.
            self.kwh_since_soc = 0.0
        if car:
            # The charged kWh as it is now (the status was made before adding).
            car = {**car, "charged_kwh": round(self.charged_kwh, 1) if self.charging_since else car.get("charged_kwh"),
                   "cost": round(self.cost, 2) if self.charging_since and self.priced else car.get("cost")}
        self.notifier.update(_cfg(self.hass), car, status.get("price"))
        async_dispatcher_send(self.hass, SIGNAL_ENERGY)

    @staticmethod
    def grid_share(status: dict[str, Any], kwh: float, hours: float) -> float:
        """The part of these kWh that came from the grid: at most what the
        house as a whole takes from the grid (consumed − returned, over all
        phases) during that time."""
        detail = status.get("phase_detail") or {}
        used = [d.get("consumed") for d in detail.values()]
        if not used or any(u is None for u in used):
            return kwh
        back = [d.get("produced") for d in detail.values()]
        # "Consumed" may be a signed net sensor (negative while returning, e.g.
        # Enphase's "Net Power Consumption") with no separate "returned" sensor;
        # without solar the house's import always covers the car: all grid.
        net_kw = (sum(used) - sum(b or 0 for b in back)) / 1000  # the house's import from the grid now
        return min(kwh, max(0.0, net_kw) * hours)

    def _debug(self, cfg: dict[str, Any], phase: str, phase_w: Any, on_phase: list[tuple[str, float]],
               est_kw: Any, from_kw: float, car_says: Any, plugged: Any, soc: Any) -> dict[str, Any]:
        """Everything that goes into "is the car charging?", for the panel's debug view."""
        hass = self.hass

        def ent(entity: str | None) -> dict[str, Any] | None:
            if not entity:
                return None
            st = hass.states.get(entity)
            return {"entity": entity, "state": st.state if st else "missing",
                    "unit": st.attributes.get("unit_of_measurement") if st else None,
                    "name": st.attributes.get("friendly_name") if st else None,
                    "changed": st.last_changed.isoformat() if st else None}

        three = int(_num(cfg.get("phases"), 1)) == 3
        return {
            "phases": 3 if three else 1,
            "charger_phase": phase,
            "consumed": ent((cfg.get("phase_sensors") or {}).get(phase)),
            "returned": ent((cfg.get("produced_sensors") or {}).get(phase)),
            "solar": ent((cfg.get("solar_sensors") or {}).get(phase)) or ent(cfg.get("solar_sensor")),
            "battery": ent(cfg.get("battery_sensor")),
            "house_on_phase_w": phase_w,
            "rooms_on_phase": [{"area": a, "watts": w} for a, w in on_phase],
            "estimate_kw": est_kw,
            "charge_from_kw": from_kw,
            "charger_max_kw": _num(cfg.get("charger_max_kw"), 3.7),
            "car_charging_sensor": ent(cfg.get("charging_sensor")),
            "car_says_charging": car_says,
            "plug_sensor": ent(cfg.get("plug_sensor")),
            "plugged": plugged,
            "soc_sensor": ent(cfg.get("soc_sensor")),
            "soc": soc,
            "session_since": self.charging_since.isoformat() if self.charging_since else None,
            "session_kwh": round(self.charged_kwh, 3),
            "checked_at": dt_util.utcnow().isoformat(),
        }

    def history(self) -> dict[str, Any]:
        """Totals for today (the running session included), this month, the
        last 30 and 365 days, and the sessions of the last 365 days, newest
        first, each with its average grid price."""
        now = dt_util.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month = today.replace(day=1)
        running = None
        if self.charging_since is not None:
            running = {"start": self.charging_since.isoformat(), "end": dt_util.utcnow().isoformat(),
                       "kwh": round(self.charged_kwh, 2), "grid_kwh": round(self.grid_kwh, 2),
                       "solar_kwh": round(self.solar_kwh, 2), "battery_kwh": None,
                       "cost": round(self.cost, 2) if self.priced else None,
                       "saved": round(self.saved, 2) if self.priced else None, "running": True}

        def total(rows: list[dict[str, Any]]) -> dict[str, Any]:
            costs = [r["cost"] for r in rows if r.get("cost") is not None]
            return {"count": len(rows), "kwh": round(sum(r.get("kwh") or 0 for r in rows), 1),
                    "grid_kwh": round(sum(r.get("grid_kwh", r.get("kwh")) or 0 for r in rows), 1),
                    "solar_kwh": round(sum(r.get("solar_kwh") or 0 for r in rows), 1),
                    "battery_kwh": round(sum(r.get("battery_kwh") or 0 for r in rows), 1),
                    "cost": round(sum(costs), 2) if costs else None,
                    "saved": round(sum(r["saved"] for r in rows if r.get("saved") is not None), 2)
                    if any(r.get("saved") is not None for r in rows) else None}

        rows = self.sessions + ([running] if running else [])

        def after(when: datetime) -> list[dict[str, Any]]:
            return [r for r in rows if (t := dt_util.parse_datetime(r.get("end") or "")) and t >= when]

        def with_price(r: dict[str, Any]) -> dict[str, Any]:
            grid = r.get("grid_kwh", r.get("kwh")) or 0
            price = round(r["cost"] / grid, 3) if r.get("cost") is not None and grid > 0 else None
            return {**r, "price": price}

        year = after(now - timedelta(days=365))
        return {
            "today": total(after(today)), "month": total(after(month)),
            "days30": total(after(now - timedelta(days=30))), "days365": total(year),
            "all": total(self.sessions),
            "days": _num(_cfg(self.hass).get("history_days"), 365),
            "sessions": [with_price(r) for r in reversed(year)][:500],
        }

    def status(self) -> dict[str, Any]:
        """For the panel: per room its power and phase; per phase its power; the car."""
        hass = self.hass
        cfg = _cfg(hass)
        three = int(_num(cfg.get("phases"), 1)) == 3
        managed = managed_areas(hass)
        rooms: dict[str, Any] = {}
        for room in hass.data.get(DOMAIN, {}).get("rooms", []):
            area = room.get("area_id")
            if area not in managed:
                continue
            parts = room_parts(hass, room)
            rooms[area] = {
                "phase": (room.get("phase") if three else "L1") or None,
                "watts": round(sum(p["watts"] or 0 for p in parts), 1),
                "parts": [{**p, "watts": None if p["watts"] is None else round(p["watts"], 1)} for p in parts],
            }
        sensors = cfg.get("phase_sensors") or {}
        produced = cfg.get("produced_sensors") or {}
        names = PHASES if three else ("L1",)
        gen = bool(cfg.get("has_solar") or cfg.get("has_battery"))

        def share(sensor_key: str, phase_key: str, on: bool) -> dict[str, float]:
            """A solar / battery output spread over the phases it is on."""
            w = _watts(hass, cfg.get(sensor_key)) if on else None
            if w is None:
                return {}
            where = cfg.get(phase_key) or "all"
            if not three:
                return {"L1": w}
            return {p: w / 3 for p in names} if where == "all" else {where: w}

        per_phase_solar = {p: x for p, x in (cfg.get("solar_sensors") or {}).items() if x and p in names}
        if cfg.get("has_solar") and per_phase_solar:
            solar = {p: w for p, x in per_phase_solar.items() if (w := _watts(hass, x)) is not None}
        else:
            solar = share("solar_sensor", "solar_phase", bool(cfg.get("has_solar")))
        battery = share("battery_sensor", "battery_phase", bool(cfg.get("has_battery")))
        detail: dict[str, Any] = {}
        phases: dict[str, float | None] = {}
        for p in names:
            if not sensors.get(p):
                continue
            used = _watts(hass, sensors.get(p))
            back = _watts(hass, produced.get(p)) if gen and produced.get(p) else None
            if used is None:
                phases[p] = None
            else:
                phases[p] = round(used - (back or 0) + solar.get(p, 0) + battery.get(p, 0), 1)
            detail[p] = {"consumed": used, "produced": back,
                         "solar": round(solar[p], 1) if p in solar else None,
                         "battery": round(battery[p], 1) if p in battery else None}
        out: dict[str, Any] = {"configured": bool(phases), "three": three, "phases": phases,
                               "phase_detail": detail, "rooms": rooms}
        charger_phase = (cfg.get("charger_phase") or "L1") if three else "L1"
        if not cfg.get("charger_room") and not cfg.get("soc_sensor"):
            if cfg.get("price_sensor"):
                out["price"] = price_status(hass, cfg, {"battery_kwh": _num(cfg.get("battery_kwh"), 8.8)}, self.sun)
            return out
        phase_w = phases.get(charger_phase)
        on_phase = [(a, r["watts"]) for a, r in rooms.items() if r["phase"] == charger_phase]
        est_kw = None if phase_w is None else max(0.0, (phase_w - sum(w for _, w in on_phase)) / 1000)
        soc = None
        if (st := hass.states.get(cfg.get("soc_sensor") or "")) is not None:
            try:
                soc = float(st.state)
            except (TypeError, ValueError):
                soc = None
        charging_state = None
        if (st := hass.states.get(cfg.get("charging_sensor") or "")) is not None and st.state not in ("unknown", "unavailable"):
            charging_state = str(st.state).lower() in CHARGING_STATES
        plugged = None
        if (st := hass.states.get(cfg.get("plug_sensor") or "")) is not None and st.state not in ("unknown", "unavailable"):
            plugged = str(st.state).lower() in ("on", "connected", "plugged", "true", "locked")
        from_kw = _num(cfg.get("charge_from_kw"), 1.2)
        # The power drawn decides (the car's own sensor, e.g. Audi Connect, is
        # often minutes late): above the limit the car is charging. The car's
        # sensor can only add to that (it says charging while the estimate is low).
        by_power = est_kw is not None and est_kw >= from_kw
        charging = by_power or charging_state is True
        why = ("power" if by_power else "car") if charging else (
            "no_phase_sensor" if phase_w is None else "below_limit")
        battery = _num(cfg.get("battery_kwh"), 8.8)
        # Charging: the estimate when it is plausible, else the charger's maximum.
        kw = (est_kw if est_kw is not None and est_kw >= from_kw else _num(cfg.get("charger_max_kw"), 3.7)) if charging else 0.0
        # The battery level now: the car's last reading plus what went in since
        # (charging losses of about 10% left out).
        soc_est = None
        if soc is not None:
            soc_est = round(min(100.0, soc + self.kwh_since_soc * CHARGE_EFFICIENCY / battery * 100), 1) if battery else soc
        soc_at = st.last_updated.isoformat() if (st := hass.states.get(cfg.get("soc_sensor") or "")) is not None else None
        full_at = None
        if charging and soc_est is not None and kw:
            hours = max(0.0, (100 - soc_est) / 100 * battery / kw)
            full_at = (dt_util.now() + timedelta(hours=hours)).isoformat()
        out["car"] = {
            "name": (cfg.get("car_name") or "").strip(),
            "room": cfg.get("charger_room"), "phase": charger_phase,
            "charging": bool(charging), "kw": round(kw, 2) if kw else 0.0,
            "estimate_kw": None if est_kw is None else round(est_kw, 2),
            "from_sensor": charging_state is not None,
            "soc": soc, "battery_kwh": battery, "soc_est": soc_est, "soc_at": soc_at,
            "kwh_since_soc": round(self.kwh_since_soc, 2),
            "kwh": None if soc_est is None else round(soc_est / 100 * battery, 1),
            "plugged": plugged, "full_at": full_at,
            "since": self.charging_since.isoformat() if self.charging_since else None,
            "charged_kwh": round(self.charged_kwh, 1) if self.charging_since else None,
            "cost": round(self.cost, 2) if self.charging_since and self.priced else None,
            "grid_kwh": round(self.grid_kwh, 1) if self.charging_since else None,
            "solar_kwh": round(self.solar_kwh, 1) if self.charging_since else None,
            "price_kwh": self.price_kwh(),
            "phase_watts": phase_w, "phase_detail": detail.get(charger_phase) or {},
            "minus": [{"area": a, "watts": w} for a, w in on_phase],
            "why": why, "from_kw": from_kw, "car_says": charging_state,
            "debug": self._debug(cfg, charger_phase, phase_w, on_phase, est_kw, from_kw, charging_state, plugged, soc),
        }
        if cfg.get("price_sensor"):
            out["price"] = price_status(hass, cfg, out["car"], self.sun)
        out["history"] = self.history()
        return out
