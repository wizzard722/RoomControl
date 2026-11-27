"""Heating with RoomMind: the schedule a room (or the house) uses, rules that
switch it, and what an electric heater's power would have cost as gas.

RoomMind (a separate integration) heats each room through its thermostat
climate.roommind_<area>, following one or more schedule helpers; a selector
(input_number, value 1 = first schedule, 2 = second, ...; or input_boolean:
off = 1, on = 2) chooses the schedule. RoomControl only reads and sets those.

Room option "heating":
 {"climate": climate entity,
  "scope": "room" (own selector) | "house" (the general one),
  "selector": input_number / input_boolean (scope "room"),
  "schedules": [schedule.*, ...] in selector order (for names and preview),
  "rules": {"armed_away": n, "vacation": n, "nobody": n, "armed_home": n,
            "armed_night": n, "leave": n, "holiday": n, "disarmed": n} (value to switch to),
  "nobody_h": hours nobody home before "nobody" applies (default 2),
  "tile": bool (Overview card, default True),
  "device_night": {climate: {"fan_mode", "swing_mode", "swing_horizontal_mode",
                  "sleep": value}} set on a device when the alarm goes to
                  armed home (the night); missing keys are left alone,
  "device_slots": {climate: [slot, ...]} time slots (slots.py format) with
                  "set": {"hvac_mode", "temperature", "fan_mode", "swing_mode",
                  "swing_horizontal_mode", "sleep"}: set when the slot starts;
                  when it ends, what was changed is put back (unless someone
                  changed it in between; the sleep timer is left to run out),
  "devices": [climate, ...] the room's heating/cooling devices (e.g. LG ThinQ
             air conditioners), only the ones the user chose (the climates
             in the room's area are offered as suggestions),
  "device": "electric" | "heatpump"}
General setting "heating":
 {"selector": the house's selector, "names": {"1": "Normaal", ...},
  "rules": {...as for a room}, "nobody_h": hours,
  "holiday_calendar": a calendar — a day with an event on is a holiday
  (default: the Holiday integration's calendar); "holiday_dates": ["MM-DD", ...] own days,
  "gas_price": € per m³ (else Energy › bill gas price), "efficiency": % of
  the gas boiler (default 90), "gas_kwh": kWh per m³ (default 9.77),
  "cop": heat pump COP (default 3.5),
  "outdoor": [{"name", "mode": "meter" | "phase", "sensor": power sensor (W),
              "phase": "L1".."L3", "max_kw": 2.5, "units": [climate, ...]}]
             outdoor units: "meter" = their own power sensor; "phase" = no
             meter, estimated like the car charger: the use on its phase −
             the rooms on that phase − the car charging there − metered
             outdoor units on that phase − the "unknown" use of that phase
             (learned per hour of the day while none of the phase's
             estimated units runs: what is left on the phase then is the
             fridge, router, …), only while one of its indoor units heats or
             cools; at most max_kw (a safety cap, the type plate's input).
             The power is split over the running indoor units by weight:
             learned watts per unit and fan mode (Heating.ac_learn, learned
             while the unit runs alone on its outdoor unit), else a weight
             from the fan speed (fan_weight: quiet/low 0.6, mid 1.0, high
             1.4, power/turbo 1.8, auto 0.8–1.4 by how far the room is from
             its target, fan only 0.1, dry 0.7; unknown names by their place
             in the device's fan modes). The power is split over the indoor units that run and
             added to their rooms (energy.py status: part kind "ac"; energy_meter
             day "ac": kWh, and while heating "heat" for the gas comparison)}

Devices: mode and temperature of a device go through the room's RoomMind
thermostat when there is one (RoomMind sets them); fan, swing, horizontal
swing and the sleep timer (a number entity of the same device whose name or
id says "sleep") are set on the device itself.

Rules, in this order (the first that applies wins): the alarm is armed away;
vacation (the alarm is armed vacation or RoomControl's mode is "away"
(vakantie); without a vacation value, armed vacation uses the armed away
value, as before 4.0.6); nobody has been home for nobody_h hours; the alarm
is armed home; the alarm is armed night; RoomControl's mode is "home" (verlof); today
is a holiday; the alarm is disarmed. The selector is set to that rule's value.
The value it had is kept and put back when no rule applies any more, unless
someone changed the selector in between.

Gas: heat = kWh × COP (electric: 1); m³ = heat ÷ (gas_kwh × efficiency).
The kWh and their cost come from energy_meter (day "heat": the room switches
of kind "heater").
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

from .const import DOMAIN, SETTING_ALARM_ENTITY, SIGNAL_CONFIG_UPDATED, SIGNAL_VACATION

_LOGGER = logging.getLogger(__name__)

DEFAULT_EFFICIENCY = 90.0
DEFAULT_GAS_KWH = 9.77
DEFAULT_COP = 3.5
DEFAULT_NOBODY_H = 2.0
RULE_ORDER = ("armed_away", "vacation", "nobody", "armed_home", "armed_night", "leave", "holiday", "disarmed")


def _area_of(hass: HomeAssistant, entity_id: str) -> str | None:
    from homeassistant.helpers import device_registry as dr, entity_registry as er  # noqa: PLC0415

    try:
        ent = er.async_get(hass).async_get(entity_id)
    except (AttributeError, KeyError):
        return None
    if ent is None:
        return None
    if ent.area_id:
        return ent.area_id
    dev = dr.async_get(hass).async_get(ent.device_id) if ent.device_id else None
    return dev.area_id if dev else None


def room_devices(hass: HomeAssistant, room: dict[str, Any] | None) -> list[str]:
    """The room's climate devices: only the ones the user chose."""
    h = heating_cfg(room)
    if isinstance(h.get("devices"), list):
        return [d for d in h["devices"] if isinstance(d, str) and d.startswith("climate.")]
    return []


def area_climates(hass: HomeAssistant, room: dict[str, Any] | None) -> list[str]:
    """Climates in the room's area that are not the thermostat or chosen yet (suggestions)."""
    h = heating_cfg(room)
    area = (room or {}).get("area_id")
    chosen = set(room_devices(hass, room))
    thermostat = h.get("climate") or f"climate.roommind_{area}"
    return sorted(s.entity_id for s in hass.states.async_all("climate")
                  if s.entity_id != thermostat and not s.entity_id.startswith("climate.roommind_")
                  and s.entity_id not in chosen and _area_of(hass, s.entity_id) == area)


def device_room(hass: HomeAssistant, climate: str) -> str | None:
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        if climate in room_devices(hass, room):
            return room.get("area_id")
    return None


def sleep_timer(hass: HomeAssistant, climate: str) -> str | None:
    """A settable sleep timer (number) on the same device as the climate."""
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    try:
        reg = er.async_get(hass)
        ent = reg.async_get(climate)
    except (AttributeError, KeyError):
        return None
    if ent is None or not ent.device_id:
        return None
    for e in er.async_entries_for_device(reg, ent.device_id):
        if e.domain == "number" and "sleep" in " ".join(str(x or "") for x in (e.entity_id, e.translation_key, e.original_name, e.name)).lower():
            return e.entity_id
    return None


def schedule_ids(hass: HomeAssistant, entities: list[str]) -> dict[str, str]:
    """entity → the schedule helper's id (only helpers made in the UI can be edited)."""
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    out = {}
    try:
        reg = er.async_get(hass)
    except (AttributeError, KeyError):
        return out
    for e in entities:
        ent = reg.async_get(e) if isinstance(e, str) else None
        if ent is not None and ent.platform == "schedule" and ent.unique_id:
            out[e] = ent.unique_id
    return out


def schedule_entity(hass: HomeAssistant, schedule_id: str) -> str | None:
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    try:
        return er.async_get(hass).async_get_entity_id("schedule", "schedule", schedule_id)
    except (AttributeError, KeyError):
        return None


def heating_cfg(room: dict[str, Any] | None) -> dict[str, Any]:
    h = (room or {}).get("heating")
    return h if isinstance(h, dict) else {}


def general_cfg(hass: HomeAssistant) -> dict[str, Any]:
    h = hass.data.get(DOMAIN, {}).get("settings", {}).get("heating")
    return h if isinstance(h, dict) else {}


def _num(v: Any, default: float) -> float:
    return float(v) if isinstance(v, (int, float)) and v > 0 else default


def holiday_calendar(hass: HomeAssistant) -> str | None:
    """The calendar with holidays: the one set, else the Holiday integration's."""
    chosen = general_cfg(hass).get("holiday_calendar")
    if chosen:
        return chosen
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    try:
        entries = list(er.async_get(hass).entities.values())
    except (AttributeError, KeyError):  # registry not loaded
        return None
    found = sorted(e.entity_id for e in entries
                   if e.platform == "holiday" and e.domain == "calendar" and not e.disabled_by)
    return found[0] if found else None


DEFAULT_OUTDOOR_KW = 2.5


def outdoor_units(hass: HomeAssistant) -> list[dict[str, Any]]:
    return [u for u in general_cfg(hass).get("outdoor") or [] if isinstance(u, dict)]


def _unit_mode(u: dict[str, Any]) -> str:
    return "phase" if u.get("mode") == "phase" else "meter"


def metered_outdoor(hass: HomeAssistant, three: bool) -> dict[str, float]:
    """W of metered outdoor units per phase ("" = phase not set)."""
    from .energy import _watts  # noqa: PLC0415

    out: dict[str, float] = {}
    for u in outdoor_units(hass):
        if _unit_mode(u) != "meter":
            continue
        w = _watts(hass, u.get("sensor"))
        if w:
            ph = (u.get("phase") or "") if three else "L1"
            out[ph] = out.get(ph, 0.0) + max(0.0, w)
    return out


def _running(hass: HomeAssistant, climates: list[str]) -> tuple[list[str], dict[str, bool]]:
    states = {c: hass.states.get(c) for c in climates}
    on = [c for c, st in states.items() if st is not None and st.state not in ("off", "unavailable", "unknown")]
    active = [c for c in on if states[c].attributes.get("hvac_action") in ("heating", "cooling", "drying", "fan")]
    run = active or [c for c in on if states[c].attributes.get("hvac_action") is None]
    heating = {c: states[c].attributes.get("hvac_action") == "heating" or (
        states[c].state == "heat" and states[c].attributes.get("hvac_action") is None) for c in run}
    return run, heating


_FAN_WORDS = (
    (("quiet", "silent", "sleep", "stil", "low", "laag", "min"), 0.6),
    (("mid", "medium", "middle", "normal"), 1.0),
    (("high", "hoog"), 1.4),
    (("power", "turbo", "max", "boost", "strong"), 1.8),
)


def fan_weight(st: Any) -> float:
    """How much of the outdoor unit an indoor unit uses, from its mode and fan speed."""
    if st is None:
        return 1.0
    a = st.attributes
    if st.state == "fan_only" or a.get("hvac_action") == "fan":
        return 0.1
    if st.state == "dry" or a.get("hvac_action") == "drying":
        return 0.7
    fan = str(a.get("fan_mode") or "").lower()
    if not fan:
        return 1.0
    if fan == "auto":
        cur, tgt = a.get("current_temperature"), a.get("temperature")
        if isinstance(cur, (int, float)) and isinstance(tgt, (int, float)):
            return round(0.8 + 0.2 * min(3.0, abs(tgt - cur)), 2)
        return 1.0
    for words, w in _FAN_WORDS:
        if any(x in fan for x in words):
            return w
    modes = [str(m).lower() for m in a.get("fan_modes") or [] if str(m).lower() != "auto"]
    if fan in modes and len(modes) > 1:
        return round(0.6 + 1.2 * modes.index(fan) / (len(modes) - 1), 2)
    return 1.0


def _fan_key(st: Any) -> str:
    return f"{st.state}|{st.attributes.get('fan_mode') or ''}" if st is not None else ""


def outdoor_split(hass: HomeAssistant, status: dict[str, Any]) -> list[dict[str, Any]]:
    """Each outdoor unit's power now (measured or estimated) and its split over
    the indoor units that run."""
    from .energy import _watts  # noqa: PLC0415

    three = bool(status.get("three"))
    phases = status.get("phases") or {}
    rooms = status.get("rooms") or {}
    car = status.get("car") or {}
    car_w = (car.get("kw") or 0.0) * 1000 if car.get("charging") else 0.0
    metered = metered_outdoor(hass, three)
    on_phase: dict[str, float] = {}
    for r in rooms.values():
        ph = (r.get("phase") or "") if three else "L1"
        on_phase[ph] = on_phase.get(ph, 0.0) + (r.get("watts") or 0.0)
    house = sum(v for v in phases.values() if v is not None) if phases and all(v is not None for v in phases.values()) else None
    ctl = hass.data.get(DOMAIN, {}).get("heating_ctl")
    units = outdoor_units(hass)

    def rest(ph: str) -> float | None:
        """The phase minus what is known on it (rooms, car, metered outdoor units)."""
        pw = phases.get(ph)
        if pw is None:
            return None
        return pw - on_phase.get(ph, 0.0) - (car_w if car.get("phase", "L1") == ph else 0.0) - metered.get(ph, 0.0)

    runs = {i: _running(hass, [c for c in u.get("units") or [] if isinstance(c, str)]) for i, u in enumerate(units)}
    if ctl is not None:  # learn the unknown use of a phase while its estimated units are off
        for ph in {((u.get("phase") or "L1") if three else "L1") for u in units if _unit_mode(u) == "phase"}:
            if any(runs[i][0] for i, u in enumerate(units) if _unit_mode(u) == "phase" and ((u.get("phase") or "L1") if three else "L1") == ph):
                continue
            r = rest(ph)
            if r is not None:
                ctl.learn_unknown(ph, max(0.0, r))
    out = []
    for i, u in enumerate(units):
        mode = _unit_mode(u)
        run, heating = runs[i]
        ph = (u.get("phase") or "L1") if three else "L1"
        watts: float | None
        if mode == "meter":
            watts = _watts(hass, u.get("sensor"))
            watts = None if watts is None else max(0.0, watts)
        elif not run:
            watts = 0.0
        else:
            r = rest(ph)
            if r is None:
                watts = None
            else:
                unk = ctl.unknown_for(ph) if ctl is not None else 0.0
                est = r - unk
                if three and house is not None:
                    est = min(est, house - sum(on_phase.values()) - car_w - sum(metered.values()) - unk)
                watts = min(max(0.0, est), _num(u.get("max_kw"), DEFAULT_OUTDOOR_KW) * 1000)
        split: dict[str, float] = {}
        weights: dict[str, float] = {}
        if watts and run:
            states = {c: hass.states.get(c) for c in run}
            if ctl is not None and len(run) == 1:
                ctl.learn_ac(run[0], _fan_key(states[run[0]]), watts)
            learned = {c: ctl.learned_w(c, _fan_key(states[c])) if ctl is not None else None for c in run}
            heur = {c: fan_weight(states[c]) for c in run}
            ratios = [learned[c] / heur[c] for c in run if learned[c] and heur[c]]
            scale = sorted(ratios)[len(ratios) // 2] if ratios else None
            for c in run:
                weights[c] = learned[c] if learned[c] else (heur[c] * scale if scale else heur[c])
            total = sum(weights.values()) or 1.0
            split = {c: round(watts * weights[c] / total, 1) for c in run}
        out.append({"index": i, "name": u.get("name") or f"#{i + 1}", "mode": mode, "phase": ph if mode == "phase" else u.get("phase"),
                    "unknown": round(ctl.unknown_for(ph)) if ctl is not None and mode == "phase" else None,
                    "watts": None if watts is None else round(watts, 1), "split": split,
                    "heating": {c: heating.get(c, False) for c in split},
                    "weights": {c: round(w, 2) for c, w in weights.items()}})
    return out


def gas_equivalent(hass: HomeAssistant, kwh: float, eur: float | None, device: str = "electric",
                   kwh_hp: float = 0.0, eur_hp: float = 0.0) -> dict[str, Any]:
    """kWh of electricity → heat, m³ of gas and what that gas would cost.
    kwh_hp: heating by heat pumps (air conditioners), always × COP."""
    g = general_cfg(hass)
    hp_cop = _num(g.get("cop"), DEFAULT_COP)
    cop = hp_cop if device == "heatpump" else 1.0
    eff = _num(g.get("efficiency"), DEFAULT_EFFICIENCY) / 100
    per_m3 = _num(g.get("gas_kwh"), DEFAULT_GAS_KWH)
    price = g.get("gas_price")
    if not isinstance(price, (int, float)):
        bill = (hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}).get("bill") or {}
        price = bill.get("gas_price") if isinstance(bill.get("gas_price"), (int, float)) else None
    heat = kwh * cop + kwh_hp * hp_cop
    m3 = heat / (per_m3 * eff) if per_m3 * eff > 0 else 0.0
    return {"kwh": round(kwh + kwh_hp, 3), "heat": round(heat, 3), "m3": round(m3, 3),
            "eur_el": None if eur is None else round(eur + eur_hp, 2),
            "eur_gas": None if price is None else round(m3 * price, 2)}


def selector_value(hass: HomeAssistant, entity: str | None) -> int | None:
    st = hass.states.get(entity) if entity else None
    if st is None:
        return None
    if entity.startswith("input_boolean."):
        return 2 if st.state == "on" else 1 if st.state == "off" else None
    try:
        return int(round(float(st.state)))
    except (TypeError, ValueError):
        return None


def selector_range(hass: HomeAssistant, entity: str | None) -> tuple[int, int]:
    st = hass.states.get(entity) if entity else None
    if st is None or entity.startswith("input_boolean."):
        return 1, 2
    try:
        lo = int(round(float(st.attributes.get("min", 1))))
        hi = int(round(float(st.attributes.get("max", 3))))
    except (TypeError, ValueError):
        return 1, 3
    return max(0, lo), max(lo, min(hi, lo + 19))


async def async_set_selector(hass: HomeAssistant, entity: str, value: int) -> None:
    if entity.startswith("input_boolean."):
        await hass.services.async_call("input_boolean", "turn_on" if value >= 2 else "turn_off", {"entity_id": entity}, blocking=False)
    else:
        domain = entity.split(".", 1)[0]
        await hass.services.async_call(domain, "set_value", {"entity_id": entity, "value": value}, blocking=False)


class Heating:
    """Switches the RoomMind schedule selectors by the rules."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.heating")
        self.held: dict[str, dict[str, Any]] = {}  # selector → {"prev", "set", "rule"}
        self.nobody_since: str | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._watch: CALLBACK_TYPE | None = None
        self._was_home_armed: bool | None = None
        self.dev_held: dict[str, dict[str, Any]] = {}  # climate → {"key", "prev", "set"}
        self.unknown: dict[str, list[float | None]] = {}  # phase → W per hour, while the ACs are off
        self.ac_learn: dict[str, dict[str, list[float]]] = {}  # climate → {"<mode>|<fan>": [W, n]}
        self._ac_at: dict[str, datetime] = {}
        self._unk_at: dict[str, datetime] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.held = {k: v for k, v in (data.get("held") or {}).items() if isinstance(v, dict)}
        self.nobody_since = data.get("nobody_since") if isinstance(data.get("nobody_since"), str) else None
        self.dev_held = {k: v for k, v in (data.get("dev_held") or {}).items() if isinstance(v, dict)}
        self.unknown = {k: v for k, v in (data.get("unknown") or {}).items() if isinstance(v, list) and len(v) == 24}
        self.ac_learn = {k: v for k, v in (data.get("ac_learn") or {}).items() if isinstance(v, dict)}

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"held": self.held, "nobody_since": self.nobody_since,
                                              "dev_held": self.dev_held, "unknown": self.unknown,
                                              "ac_learn": self.ac_learn}, 10)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(seconds=60)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_VACATION, self._tick))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._rewatch))
        self._rewatch()

    @callback
    def shutdown(self) -> None:
        for u in self._unsubs:
            u()
        self._unsubs.clear()
        if self._watch:
            self._watch()
            self._watch = None

    @callback
    def _rewatch(self, *_: Any) -> None:
        from .rooms import household_persons  # noqa: PLC0415

        if self._watch:
            self._watch()
        settings = self.hass.data.get(DOMAIN, {}).get("settings", {})
        g = general_cfg(self.hass)
        ids = [e for e in [settings.get(SETTING_ALARM_ENTITY), holiday_calendar(self.hass)] if e]
        ids += list(household_persons(self.hass))
        self._watch = async_track_state_change_event(self.hass, ids, self._on_state) if ids else None
        self._tick()

    @callback
    def _on_state(self, _event: Event) -> None:
        self._tick()

    # ── what applies now ──────────────────────────────────────────────────

    def learn_unknown(self, phase: str, watts: float, now: datetime | None = None) -> None:
        """What is left on a phase while its estimated outdoor units are off,
        per local hour (moving average, at most every 25 s)."""
        now = now or dt_util.utcnow()
        last = self._unk_at.get(phase)
        if last is not None and (now - last).total_seconds() < 25:
            return
        self._unk_at[phase] = now
        row = self.unknown.setdefault(phase, [None] * 24)
        h = dt_util.as_local(now).hour
        row[h] = round(watts if row[h] is None else row[h] * 0.95 + watts * 0.05, 1)
        self._save()

    def learn_ac(self, climate: str, key: str, watts: float, now: datetime | None = None) -> None:
        """An indoor unit running alone on its outdoor unit: its watts for this
        mode and fan speed (moving average, at most every 25 s)."""
        if not key or watts <= 0:
            return
        now = now or dt_util.utcnow()
        last = self._ac_at.get(climate)
        if last is not None and (now - last).total_seconds() < 25:
            return
        self._ac_at[climate] = now
        rec = self.ac_learn.setdefault(climate, {}).setdefault(key, [watts, 0])
        n = min(rec[1] + 1, 40)
        rec[0] = round(rec[0] + (watts - rec[0]) / n, 1)
        rec[1] = rec[1] + 1
        self._save()

    def learned_w(self, climate: str, key: str, min_n: int = 10) -> float | None:
        """Learned watts of a unit for this mode and fan speed (after about 5 minutes alone)."""
        rec = (self.ac_learn.get(climate) or {}).get(key)
        return rec[0] if rec and rec[1] >= min_n else None

    def unknown_for(self, phase: str, now: datetime | None = None) -> float:
        row = self.unknown.get(phase) or []
        if not row:
            return 0.0
        v = row[dt_util.as_local(now or dt_util.utcnow()).hour]
        if v is not None:
            return v
        known = [x for x in row if x is not None]
        return sum(known) / len(known) if known else 0.0

    def situations(self, now: datetime | None = None) -> dict[str, Any]:
        from .rooms import anyone_home  # noqa: PLC0415

        hass = self.hass
        now = now or dt_util.utcnow()
        alarm = hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ALARM_ENTITY)
        st = hass.states.get(alarm) if alarm else None
        home = anyone_home(hass)
        if home:
            self.nobody_since = None
        elif self.nobody_since is None:
            self.nobody_since = now.isoformat()
        since = dt_util.parse_datetime(self.nobody_since) if self.nobody_since else None
        g = general_cfg(hass)
        cal_id = holiday_calendar(hass)
        cal = hass.states.get(cal_id) if cal_id else None
        today = dt_util.as_local(now).strftime("%m-%d")
        dates = {str(d) for d in g.get("holiday_dates") or []}
        mode = hass.data.get(DOMAIN, {}).get("vacation")
        return {"armed_away": st is not None and st.state == "armed_away",
                "armed_vacation": st is not None and st.state == "armed_vacation",
                "armed_home": st is not None and st.state == "armed_home",
                "armed_night": st is not None and st.state == "armed_night",
                "disarmed": st is not None and st.state == "disarmed",
                "holiday": (cal is not None and cal.state == "on") or today in dates,
                "vacation": mode == "away" or (st is not None and st.state == "armed_vacation"),
                "leave": mode == "home" or mode is True,
                "nobody_h": 0.0 if since is None else (now - since).total_seconds() / 3600}

    @staticmethod
    def wanted(cfg: dict[str, Any], sit: dict[str, Any]) -> tuple[str | None, int | None]:
        rules = cfg.get("rules") if isinstance(cfg.get("rules"), dict) else {}
        for rule in RULE_ORDER:
            value = rules.get(rule)
            if rule == "vacation" and not isinstance(value, (int, float)) and sit.get("armed_vacation"):
                value = rules.get("armed_away")  # as before: armed vacation counted as armed away
            if not isinstance(value, (int, float)):
                continue
            if rule == "nobody":
                if sit["nobody_h"] >= _num(cfg.get("nobody_h"), DEFAULT_NOBODY_H):
                    return rule, int(value)
            elif sit[rule]:
                return rule, int(value)
        return None, None

    def targets(self) -> list[tuple[str, dict[str, Any], str | None]]:
        """(selector, config with the rules, area or None for the house)."""
        out = []
        g = general_cfg(self.hass)
        if g.get("selector"):
            out.append((g["selector"], g, None))
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            h = heating_cfg(room)
            if h.get("scope", "room") == "room" and h.get("selector") and h["selector"] != g.get("selector"):
                out.append((h["selector"], h, room.get("area_id")))
        return out

    @callback
    def _tick(self, *_: Any) -> None:
        sit = self.situations()
        night = sit["armed_home"] or sit["armed_night"]  # the devices' night settings
        if night and self._was_home_armed is False:
            self._night_devices()
        self._was_home_armed = night
        try:
            self._device_slots()
        except Exception:  # noqa: BLE001 - never break the schedule rules
            _LOGGER.exception("Heating: device time slots failed")
        seen = set()
        for sel, cfg, area in self.targets():
            seen.add(sel)
            rule, want = self.wanted(cfg, sit)
            cur = selector_value(self.hass, sel)
            held = self.held.get(sel)
            if want is not None:
                if held is None:
                    self.held[sel] = {"prev": cur, "set": want, "rule": rule}
                    if cur != want:
                        self._set(sel, want, rule, area)
                elif held.get("set") != want:
                    held.update(set=want, rule=rule)
                    self._set(sel, want, rule, area)
            elif held is not None:
                del self.held[sel]
                if cur == held.get("set") and isinstance(held.get("prev"), int) and held["prev"] != cur:
                    self._set(sel, held["prev"], "back", area)
        for sel in [s for s in self.held if s not in seen]:
            del self.held[sel]
        self._save()

    def _device_slots(self, now: datetime | None = None) -> None:
        """Device time slots: set at the start, put back at the end."""
        import json  # noqa: PLC0415

        from .slots import mode_slots, slot_part  # noqa: PLC0415
        from .switch import _sun_phase  # noqa: PLC0415

        phase, sun_down = _sun_phase(self.hass)
        now = dt_util.as_local(now or dt_util.now())
        vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
        seen = set()
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            h = heating_cfg(room)
            via = (h.get("climate") or "").startswith("climate.roommind_") or bool(
                self.hass.states.get(f"climate.roommind_{room.get('area_id')}"))
            slots = h.get("device_slots") if isinstance(h.get("device_slots"), dict) else {}
            for climate, items in slots.items():
                if not isinstance(items, list):
                    continue
                seen.add(climate)
                active = next(((i, x) for i, x in enumerate(items) if isinstance(x, dict)
                               and x in mode_slots(items, vacation) and slot_part(x, now, phase, sun_down) is not None), None)
                held = self.dev_held.get(climate)
                if active is not None:
                    want = {k: v for k, v in (active[1].get("set") or {}).items() if v not in (None, "")}
                    if via:
                        want.pop("hvac_mode", None)
                        want.pop("temperature", None)
                    key = f"{active[0]}|{json.dumps(want, sort_keys=True)}"
                    if held is None or held.get("key") != key:
                        prev = held["prev"] if held else self._device_now(climate)
                        self.dev_held[climate] = {"key": key, "prev": prev, "set": want}
                        self._device_apply(climate, want, room.get("area_id"), "heating_slot")
                elif held is not None:
                    del self.dev_held[climate]
                    cur = self._device_now(climate)
                    back = {k: held["prev"][k] for k, v in held.get("set", {}).items()
                            if k != "sleep" and k in held.get("prev", {}) and cur.get(k) == v and held["prev"][k] != v}
                    if back:
                        self._device_apply(climate, back, room.get("area_id"), "heating_slot_end")
        for climate in [c for c in self.dev_held if c not in seen]:
            del self.dev_held[climate]

    def _device_now(self, climate: str) -> dict[str, Any]:
        st = self.hass.states.get(climate)
        if st is None:
            return {}
        a = st.attributes
        return {"hvac_mode": st.state, "temperature": a.get("temperature"), "fan_mode": a.get("fan_mode"),
                "swing_mode": a.get("swing_mode"), "swing_horizontal_mode": a.get("swing_horizontal_mode")}

    def _device_apply(self, climate: str, values: dict[str, Any], area: str | None, reason: str) -> None:
        st = self.hass.states.get(climate)
        if st is None or st.state == "unavailable":
            return
        a = st.attributes
        calls: list[tuple[str, str, dict[str, Any]]] = []
        if values.get("hvac_mode") in (a.get("hvac_modes") or []) and st.state != values["hvac_mode"]:
            calls.append(("climate", "set_hvac_mode", {"hvac_mode": values["hvac_mode"]}))
        if isinstance(values.get("temperature"), (int, float)) and a.get("temperature") != values["temperature"]:
            calls.append(("climate", "set_temperature", {"temperature": values["temperature"]}))
        for attr, service, options in (("fan_mode", "set_fan_mode", "fan_modes"), ("swing_mode", "set_swing_mode", "swing_modes"),
                                       ("swing_horizontal_mode", "set_swing_horizontal_mode", "swing_horizontal_modes")):
            v = values.get(attr)
            if v and v in (a.get(options) or []) and a.get(attr) != v:
                calls.append(("climate", service, {attr: v}))
        for domain, service, data in calls:
            self.hass.async_create_task(self.hass.services.async_call(domain, service, {"entity_id": climate, **data}, blocking=False))
        timer = sleep_timer(self.hass, climate)
        if timer and isinstance(values.get("sleep"), (int, float)):
            self.hass.async_create_task(self.hass.services.async_call(
                "number", "set_value", {"entity_id": timer, "value": values["sleep"]}, blocking=False))
        light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(area)
        if light is not None and hasattr(light, "_debug") and (calls or timer):
            light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": "info", "reason": reason,
                                 "bundles": [a.get("friendly_name") or climate], "items": [climate]})

    def _night_devices(self) -> None:
        """Alarm went to armed home: each device's night settings."""
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            night = heating_cfg(room).get("device_night")
            if not isinstance(night, dict):
                continue
            for climate, cfg in night.items():
                st = self.hass.states.get(climate)
                if st is None or st.state in ("off", "unavailable") or not isinstance(cfg, dict):
                    continue
                for attr, service, options in (("fan_mode", "set_fan_mode", "fan_modes"),
                                               ("swing_mode", "set_swing_mode", "swing_modes"),
                                               ("swing_horizontal_mode", "set_swing_horizontal_mode", "swing_horizontal_modes")):
                    value = cfg.get(attr)
                    if value and value in (st.attributes.get(options) or []) and st.attributes.get(attr) != value:
                        self.hass.async_create_task(self.hass.services.async_call(
                            "climate", service, {"entity_id": climate, attr: value}, blocking=False))
                timer = sleep_timer(self.hass, climate)
                if timer and isinstance(cfg.get("sleep"), (int, float)):
                    self.hass.async_create_task(self.hass.services.async_call(
                        "number", "set_value", {"entity_id": timer, "value": cfg["sleep"]}, blocking=False))
                light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(room.get("area_id"))
                if light is not None and hasattr(light, "_debug"):
                    light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": "info", "reason": "heating_night",
                                         "bundles": [st.attributes.get("friendly_name") or climate], "items": [climate]})

    def _set(self, sel: str, value: int, rule: str | None, area: str | None) -> None:
        _LOGGER.debug("Heating: %s → %s (%s)", sel, value, rule)
        self.hass.async_create_task(async_set_selector(self.hass, sel, value))
        areas = [area] if area else [r.get("area_id") for r in self.hass.data.get(DOMAIN, {}).get("rooms", [])
                                     if heating_cfg(r).get("climate") and heating_cfg(r).get("scope") == "house"]
        name = schedule_name(self.hass, area, value)
        for a in areas:
            light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(a)
            if light is not None and hasattr(light, "_debug"):
                light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": "info",
                                     "reason": f"heating_{rule or 'back'}", "bundles": [name], "items": [sel]})


def schedule_name(hass: HomeAssistant, area: str | None, value: int) -> str:
    """The name of schedule `value`: the room's schedule helper, else the general name."""
    room = next((r for r in hass.data.get(DOMAIN, {}).get("rooms", []) if r.get("area_id") == area), None)
    scheds = heating_cfg(room).get("schedules") or []
    if 1 <= value <= len(scheds):
        st = hass.states.get(scheds[value - 1])
        if st is not None:
            return st.attributes.get("friendly_name") or scheds[value - 1]
    name = (general_cfg(hass).get("names") or {}).get(str(value))
    return f"{value} · {name}" if name else str(value)


def room_status(hass: HomeAssistant, area: str) -> dict[str, Any]:
    """Panel: the room's thermostat, selector, schedules, heaters and gas."""
    from .room_switches import room_switches  # noqa: PLC0415

    room = next((r for r in hass.data.get(DOMAIN, {}).get("rooms", []) if r.get("area_id") == area), None) or {}
    h = heating_cfg(room)
    g = general_cfg(hass)
    climate = h.get("climate") or (f"climate.roommind_{area}" if hass.states.get(f"climate.roommind_{area}") else None)
    st = hass.states.get(climate) if climate else None
    sel = g.get("selector") if h.get("scope") == "house" else h.get("selector")
    lo, hi = selector_range(hass, sel)
    heaters = [sw["entity_id"] for sw in room_switches(room) if sw["kind"] == "heater"]
    meter = hass.data.get(DOMAIN, {}).get("meter")
    energy = hass.data.get(DOMAIN, {}).get("energy")
    status = (getattr(energy, "last_status", None) or {}) if energy else {}
    parts = {p["key"]: p for p in ((status.get("rooms") or {}).get(area) or {}).get("parts") or []}
    device = h.get("device") if h.get("device") in ("electric", "heatpump") else "electric"
    totals = meter.heat_totals(area) if meter is not None else {}
    held = (hass.data.get(DOMAIN, {}).get("heating_ctl") or Heating(hass)).held.get(sel or "") if sel else None
    return {
        "climate": climate,
        "found": f"climate.roommind_{area}" if hass.states.get(f"climate.roommind_{area}") else None,
        "thermostat": None if st is None else {
            "state": st.state, "current": st.attributes.get("current_temperature"),
            "target": st.attributes.get("temperature"), "action": st.attributes.get("hvac_action"),
            "target_low": st.attributes.get("target_temp_low"), "target_high": st.attributes.get("target_temp_high"),
            "preset": st.attributes.get("preset_mode"), "presets": st.attributes.get("preset_modes") or [],
            "override_until": st.attributes.get("override_until"), "window_open": st.attributes.get("window_open"),
            "presence_away": st.attributes.get("presence_away"), "name": st.attributes.get("friendly_name")},
        "selector": sel, "value": selector_value(hass, sel), "min": lo, "max": hi,
        "names": {str(v): schedule_name(hass, area, v) for v in range(max(1, lo), hi + 1)},
        "held": held,
        "heaters": [{"entity": e, "name": (hass.states.get(e).attributes.get("friendly_name") if hass.states.get(e) else e),
                     "watts": (parts.get(f"switch:{e}") or {}).get("watts"),
                     "on": bool(hass.states.get(e) and hass.states.get(e).state == "on")} for e in heaters],
        "gas": {k: gas_equivalent(hass, v["kwh"], v.get("eur"), device, v.get("kwh_hp", 0.0), v.get("eur_hp", 0.0))
                for k, v in totals.items()},
        "device": device,
        "via_roommind": bool(climate and climate.startswith("climate.roommind_") and st is not None),
        "explicit": isinstance(h.get("devices"), list),
        "schedule_ids": schedule_ids(hass, h.get("schedules") or []),
        "devices": [_with_share(device_status(hass, c, meter.device_today(area, c) if meter is not None else None), outdoor_now(hass))
                    for c in room_devices(hass, room)],
        "outdoor": outdoor_now(hass),
        "suggest": [{"entity": c, "name": (hass.states.get(c).attributes.get("friendly_name") if hass.states.get(c) else None) or c}
                    for c in area_climates(hass, room)],
        "three": int(_num((hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}).get("phases"), 1)) == 3,
    }


def outdoor_now(hass: HomeAssistant) -> list[dict[str, Any]]:
    """The outdoor units with their power now (from the last energy tick)."""
    energy = hass.data.get(DOMAIN, {}).get("energy")
    last = {u["index"]: u for u in ((getattr(energy, "last_status", None) or {}).get("outdoor") or [])} if energy else {}
    return [{**u, "watts": (last.get(i) or {}).get("watts"), "unknown": (last.get(i) or {}).get("unknown"),
             "split": (last.get(i) or {}).get("split") or {}, "weights": (last.get(i) or {}).get("weights") or {},
             "unit": "W", "estimated": _unit_mode(u) == "phase"}
            for i, u in enumerate(outdoor_units(hass))]


def _with_share(dev: dict[str, Any], units: list[dict[str, Any]]) -> dict[str, Any]:
    """The device's outdoor unit and its share of it now."""
    for u in units:
        if dev["entity"] in (u.get("units") or []):
            return {**dev, "outdoor": {"name": u.get("name"), "watts": u.get("watts"), "estimated": u.get("estimated"),
                                       "phase": u.get("phase")},
                    "share_w": (u.get("split") or {}).get(dev["entity"], 0.0) if u.get("watts") is not None else None,
                    "weight": (u.get("weights") or {}).get(dev["entity"])}
    return dev


def device_status(hass: HomeAssistant, climate: str, today: dict[str, Any] | None = None) -> dict[str, Any]:
    st = hass.states.get(climate)
    a = st.attributes if st is not None else {}
    timer = sleep_timer(hass, climate)
    ts = hass.states.get(timer) if timer else None
    return {
        "entity": climate, "name": a.get("friendly_name") or climate, "state": st.state if st is not None else None,
        "action": a.get("hvac_action"), "current": a.get("current_temperature"), "target": a.get("temperature"),
        "target_low": a.get("target_temp_low"), "target_high": a.get("target_temp_high"),
        "min": a.get("min_temp"), "max": a.get("max_temp"), "step": a.get("target_temp_step"),
        "hvac_modes": a.get("hvac_modes") or [],
        "fan": a.get("fan_mode"), "fan_modes": a.get("fan_modes") or [],
        "swing": a.get("swing_mode"), "swing_modes": a.get("swing_modes") or [],
        "hswing": a.get("swing_horizontal_mode"), "hswing_modes": a.get("swing_horizontal_modes") or [],
        "preset": a.get("preset_mode"), "presets": a.get("preset_modes") or [],
        "sleep": None if ts is None else {"entity": timer, "value": _float(ts.state), "min": ts.attributes.get("min"),
                                          "max": ts.attributes.get("max"), "step": ts.attributes.get("step"),
                                          "unit": ts.attributes.get("unit_of_measurement")},
        "today": today,
        "learned": {k: round(v[0]) for k, v in ((hass.data.get(DOMAIN, {}).get("heating_ctl").ac_learn.get(climate) or {})
                                              if hass.data.get(DOMAIN, {}).get("heating_ctl") is not None else {}).items() if v[1] >= 10},
    }


def _float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def house_status(hass: HomeAssistant) -> dict[str, Any]:
    """Panel (general settings): the house selector and this month's heaters as gas."""
    g = general_cfg(hass)
    sel = g.get("selector")
    lo, hi = selector_range(hass, sel)
    meter = hass.data.get(DOMAIN, {}).get("meter")
    month = (meter.heat_totals(None) if meter is not None else {}).get("month") or {"kwh": 0.0, "eur": None}
    rooms = []
    for r in hass.data.get(DOMAIN, {}).get("rooms", []):
        h = heating_cfg(r)
        climate = h.get("climate") or (f"climate.roommind_{r.get('area_id')}" if hass.states.get(f"climate.roommind_{r.get('area_id')}") else None)
        if climate or h:
            rooms.append({"area": r.get("area_id"), "climate": climate, "scope": h.get("scope", "room"), "selector": h.get("selector")})
    found = sorted(s.entity_id for s in hass.states.async_all("climate") if s.entity_id.startswith("climate.roommind_"))
    ctl = hass.data.get(DOMAIN, {}).get("heating_ctl") or Heating(hass)
    sit = ctl.situations()
    outdoor = outdoor_now(hass)
    climates = sorted({c for r in hass.data.get(DOMAIN, {}).get("rooms", []) for c in room_devices(hass, r)}
                      | {c for u in g.get("outdoor") or [] if isinstance(u, dict) for c in u.get("units") or []})
    return {"selector": sel, "value": selector_value(hass, sel), "min": lo, "max": hi, "rooms": rooms,
            "outdoor": outdoor, "climates": climates,
            "now": {k: sit[k] for k in ("armed_away", "armed_home", "armed_night", "holiday", "vacation", "leave", "disarmed")},
            "holiday_calendar": holiday_calendar(hass), "held": ctl.held.get(sel) if sel else None,
            "roommind": found, "month": gas_equivalent(hass, month["kwh"], month.get("eur"), "electric", month.get("kwh_hp", 0.0), month.get("eur_hp", 0.0))}
