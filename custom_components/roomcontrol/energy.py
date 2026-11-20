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
 "soc_sensor": sensor (%), "charging_sensor": entity, "plug_sensor": entity}  # optional

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
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import CONF_GROUPS, DOMAIN
from .rooms import managed_areas

SETTING_ENERGY = "energy"
SIGNAL_ENERGY = "roomcontrol_energy"  # sent after each check (every 30 s)
PHASES = ("L1", "L2", "L3")
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
    found = []
    for other in er.async_entries_for_device(ent_reg, entry.device_id):
        if other.domain != "sensor" or other.disabled_by:
            continue
        st = hass.states.get(other.entity_id)
        have = str((st.attributes.get("unit_of_measurement") if st else None) or other.unit_of_measurement or "").lower()
        if have == unit:
            found.append(other.entity_id)
    return sorted(found)[0] if found else None


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
    return out


class Energy:
    """Keeps track of the car's charging: since when, and how much."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsub: CALLBACK_TYPE | None = None
        self.charging_since: datetime | None = None
        self.charged_kwh = 0.0
        self._last: datetime | None = None

    @callback
    def start(self) -> None:
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(seconds=30))

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _tick(self, _now: Any = None) -> None:
        status = self.status()
        car = status.get("car") or {}
        now = dt_util.utcnow()
        if car.get("charging"):
            if self.charging_since is None:
                self.charging_since, self.charged_kwh = now, 0.0
            elif self._last is not None and car.get("kw"):
                self.charged_kwh += car["kw"] * (now - self._last).total_seconds() / 3600
            self._last = now
        else:
            self.charging_since, self._last = None, None
        async_dispatcher_send(self.hass, SIGNAL_ENERGY)

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
        charging = charging_state if charging_state is not None else (est_kw is not None and est_kw >= from_kw)
        battery = _num(cfg.get("battery_kwh"), 8.8)
        # Charging: the estimate when it is plausible, else the charger's maximum.
        kw = (est_kw if est_kw is not None and est_kw >= from_kw else _num(cfg.get("charger_max_kw"), 3.7)) if charging else 0.0
        full_at = None
        if charging and soc is not None and kw:
            hours = max(0.0, (100 - soc) / 100 * battery / kw)
            full_at = (dt_util.now() + timedelta(hours=hours)).isoformat()
        out["car"] = {
            "name": (cfg.get("car_name") or "").strip(),
            "room": cfg.get("charger_room"), "phase": charger_phase,
            "charging": bool(charging), "kw": round(kw, 2) if kw else 0.0,
            "estimate_kw": None if est_kw is None else round(est_kw, 2),
            "from_sensor": charging_state is not None,
            "soc": soc, "battery_kwh": battery,
            "kwh": None if soc is None else round(soc / 100 * battery, 1),
            "plugged": plugged, "full_at": full_at,
            "since": self.charging_since.isoformat() if self.charging_since else None,
            "charged_kwh": round(self.charged_kwh, 1) if self.charging_since else None,
            "phase_watts": phase_w, "phase_detail": detail.get(charger_phase) or {},
            "minus": [{"area": a, "watts": w} for a, w in on_phase],
        }
        return out
