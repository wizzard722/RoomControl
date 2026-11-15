"""Room helpers shared by setup and the light platform."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_COVERS,
    CONF_COVERS_INVERTED,
    CONF_DOOR_SENSORS,
    CONF_FANS,
    CONF_FAN_SHARED_ROOMS,
    CONF_FAN_STEPS,
    CONF_LINKED_ROOMS,
    CONF_LOCKS,
    CONF_LUX_MODE,
    CONF_LUX_SENSOR,
    CONF_LUX_SENSORS,
    DEFAULT_LUX_MODE,
    CONF_MOTION_SENSOR,
    CONF_MOTION_SENSORS,
    DAYLIGHT_HIGH_ELEVATION,
    DAYLIGHT_LOW_ELEVATION,
    DAYLIGHT_MAX_KELVIN,
    DAYLIGHT_MIN_KELVIN,
    KELVIN_COLOR_MODES,
    CONF_PERSONS,
    CONF_SCHEDULE_SELECTOR,
    CONF_SCHEDULES,
    DOMAIN,
    SETTING_PERSONS,
)


@callback
def stored_room(hass: HomeAssistant, area_id: str) -> dict[str, Any] | None:
    """Saved config for an area, or None if the area was never saved."""
    rooms = hass.data.get(DOMAIN, {}).get("rooms", [])
    return next((r for r in rooms if r.get("area_id") == area_id), None)


def room_locks(room: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The room's lock settings (one per lock with an entity id)."""
    return [
        lock for lock in (room or {}).get(CONF_LOCKS, []) or []
        if isinstance(lock, dict) and lock.get("entity_id")
    ]


def room_managed(room: dict[str, Any] | None) -> bool:
    """RoomControl manages this room: it is not hidden and has lamps, motion
    or door sensors, curtains or fans. Only managed rooms get a device."""
    if not room or room.get("hidden"):
        return False
    return bool(
        any(l.get("entity_id") for l in room.get("lights", []) or [])
        or [s for s in room.get(CONF_MOTION_SENSORS, []) or [] if s]
        or room.get(CONF_MOTION_SENSOR)
        or [s for s in room.get(CONF_DOOR_SENSORS, []) or [] if s]
        or [c for c in room.get(CONF_COVERS, []) or [] if c]
        or [f for f in room.get(CONF_FANS, []) or [] if f]
        or room_locks(room)
    )


@callback
def managed_areas(hass: HomeAssistant) -> set[str]:
    """Area ids of the managed rooms whose area still exists."""
    from homeassistant.helpers import area_registry as ar

    areas = {a.id for a in ar.async_get(hass).async_list_areas()}
    return {
        r["area_id"] for r in hass.data.get(DOMAIN, {}).get("rooms", [])
        if r.get("area_id") in areas and room_managed(r)
    }


@callback
def room_lights(hass: HomeAssistant, area_id: str) -> list[str]:
    """Lights the user added to this room (none until the room is saved)."""
    room = stored_room(hass, area_id)
    if room is None:
        return []
    return [l["entity_id"] for l in room.get("lights", []) if l.get("entity_id")]


@callback
def active_schedule(hass: HomeAssistant, room: dict[str, Any] | None) -> str | None:
    """The schedule.* entity that currently limits this room, or None.

    No schedules → None. No input_number → the first schedule. Otherwise the
    input_number value picks it (1 = first). 0, out of range, or a missing or
    non-numeric input_number → None (no limit, lights stay usable).
    """
    schedules = [s for s in (room or {}).get(CONF_SCHEDULES, []) if s]
    if not schedules:
        return None
    selector = (room or {}).get(CONF_SCHEDULE_SELECTOR)
    if not selector:
        return schedules[0]
    state = hass.states.get(selector)
    try:
        index = int(float(state.state)) if state else 0
    except ValueError:
        return None
    if 1 <= index <= len(schedules):
        return schedules[index - 1]
    return None


@callback
def schedule_allows(hass: HomeAssistant, room: dict[str, Any] | None) -> bool:
    """True when lights may be on: no active schedule, or it is 'on' now.

    A schedule entity that is missing or unavailable blocks nothing.
    """
    schedule = active_schedule(hass, room)
    if schedule is None:
        return True
    state = hass.states.get(schedule)
    if state is None or state.state not in ("on", "off"):
        return True
    return state.state == "on"


@callback
def room_persons(hass: HomeAssistant, room: dict[str, Any] | None) -> list[str]:
    """Persons linked to the room that are enabled in the global settings."""
    enabled = set(hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_PERSONS, []))
    return [p for p in (room or {}).get(CONF_PERSONS, []) if p in enabled]


@callback
def presence_allows(hass: HomeAssistant, room: dict[str, Any] | None) -> bool:
    """True when no persons are linked, or at least one linked person is home."""
    persons = room_persons(hass, room)
    if not persons:
        return True
    return any((st := hass.states.get(p)) is not None and st.state == "home" for p in persons)


@callback
def dusk_override(hass: HomeAssistant, room: dict[str, Any] | None) -> bool:
    """"Turn on at dusk" is set and the sun is down: light is wanted, schedule or not."""
    room = room or {}
    if not room.get("turn_on_at_dusk"):
        return False
    sun = hass.states.get(room.get("sun_entity") or "sun.sun")
    return sun is not None and sun.state == "below_horizon"


@callback
def room_allows(hass: HomeAssistant, room: dict[str, Any] | None) -> bool:
    """Lights may be on: someone linked is home, and either the schedule
    allows it or it is dusk with "turn on at dusk" set (dusk overrides an off
    schedule)."""
    return presence_allows(hass, room) and (
        schedule_allows(hass, room) or dusk_override(hass, room)
    )


@callback
def daylight_kelvin(
    hass: HomeAssistant,
    sun_entity: str = "sun.sun",
    min_kelvin: int = DAYLIGHT_MIN_KELVIN,
    max_kelvin: int = DAYLIGHT_MAX_KELVIN,
) -> int | None:
    """Colour temperature matching the sun: warm when low, cool when high.

    Linear in the sun's elevation between DAYLIGHT_LOW/HIGH_ELEVATION, rounded
    to 50 K. None when the sun entity or its elevation is unavailable.
    """
    state = hass.states.get(sun_entity)
    elevation = state.attributes.get("elevation") if state else None
    if not isinstance(elevation, (int, float)):
        return None
    span = DAYLIGHT_HIGH_ELEVATION - DAYLIGHT_LOW_ELEVATION
    f = min(1.0, max(0.0, (elevation - DAYLIGHT_LOW_ELEVATION) / span))
    kelvin = min_kelvin + f * (max_kelvin - min_kelvin)
    return int(round(kelvin / 50) * 50)


@callback
def supports_kelvin(hass: HomeAssistant, entity_id: str) -> bool:
    """True if the light can take a colour temperature (directly or via colour)."""
    state = hass.states.get(entity_id)
    modes = state.attributes.get("supported_color_modes") if state else None
    return bool(modes) and any(str(m) in KELVIN_COLOR_MODES for m in modes)


@callback
def room_motion_sensors(room: dict[str, Any] | None) -> list[str]:
    """The room's motion sensors (list format, or the older single sensor)."""
    room = room or {}
    sensors = room.get(CONF_MOTION_SENSORS)
    if sensors is None:
        single = room.get(CONF_MOTION_SENSOR)
        sensors = [single] if single else []
    return [s for s in sensors if s]


@callback
def linked_group(hass: HomeAssistant, area_id: str, key: str = CONF_LINKED_ROOMS) -> list[str]:
    """area_id plus every room linked to it (via `key`), directly or via other rooms.

    A link counts both ways, whichever room it was set on.
    """
    rooms = hass.data.get(DOMAIN, {}).get("rooms", [])
    neighbours: dict[str, set[str]] = {}
    for room in rooms:
        a = room.get("area_id")
        for b in room.get(key, []) or []:
            if a and b and a != b:
                neighbours.setdefault(a, set()).add(b)
                neighbours.setdefault(b, set()).add(a)
    group, todo = {area_id}, [area_id]
    while todo:
        for nxt in neighbours.get(todo.pop(), ()):
            if nxt not in group:
                group.add(nxt)
                todo.append(nxt)
    return sorted(group)


@callback
def group_motion_sensors(hass: HomeAssistant, area_id: str) -> list[str]:
    """Motion sensors of the room and all rooms linked to it."""
    sensors: list[str] = []
    for member in linked_group(hass, area_id):
        for sensor in room_motion_sensors(stored_room(hass, member)):
            if sensor not in sensors:
                sensors.append(sensor)
    return sensors


@callback
def fan_group(hass: HomeAssistant, area_id: str) -> list[str]:
    """area_id plus every room it shares its fans with (directly or via others)."""
    return linked_group(hass, area_id, CONF_FAN_SHARED_ROOMS)


@callback
def room_fans(hass: HomeAssistant, area_id: str) -> list[str]:
    """The room's own fans plus those of the rooms it shares fans with."""
    fans: list[str] = []
    own_first = [area_id] + [a for a in fan_group(hass, area_id) if a != area_id]
    for member in own_first:
        for fan in (stored_room(hass, member) or {}).get(CONF_FANS, []) or []:
            if fan and fan not in fans:
                fans.append(fan)
    return fans


@callback
def room_fan_steps(hass: HomeAssistant, area_id: str) -> list[dict[str, Any]]:
    """The room's own fan steps; none → those of a room it shares fans with."""
    own = (stored_room(hass, area_id) or {}).get(CONF_FAN_STEPS) or []
    if own:
        return own
    for member in fan_group(hass, area_id):
        if member != area_id and (steps := (stored_room(hass, member) or {}).get(CONF_FAN_STEPS) or []):
            return steps
    return []


@callback
def room_lux_sensors(room: dict[str, Any] | None) -> list[str]:
    """The room's lux sensors (list format, or the older single sensor)."""
    room = room or {}
    sensors = room.get(CONF_LUX_SENSORS)
    if sensors is None:
        single = room.get(CONF_LUX_SENSOR)
        sensors = [single] if single else []
    return [s for s in sensors if s]


def combine_lux(values: list[float], mode: str | None) -> float | None:
    """Combine sensor readings: average (default), min, max, median or sum."""
    if not values:
        return None
    mode = mode or DEFAULT_LUX_MODE
    if mode == "min":
        return min(values)
    if mode == "max":
        return max(values)
    if mode == "sum":
        return sum(values)
    if mode == "median":
        ordered = sorted(values)
        mid = len(ordered) // 2
        return ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    return sum(values) / len(values)


@callback
def room_lux(hass: HomeAssistant, room: dict[str, Any] | None) -> float | None:
    """The room's lux: its sensors combined; sensors without a number are skipped."""
    values: list[float] = []
    for sensor in room_lux_sensors(room):
        state = hass.states.get(sensor)
        try:
            values.append(float(state.state)) if state else None
        except ValueError:
            pass
    return combine_lux(values, (room or {}).get(CONF_LUX_MODE))


@callback
def household_persons(hass: HomeAssistant) -> list[str]:
    """All persons enabled in the global settings."""
    return [p for p in hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_PERSONS, []) if p]


@callback
def anyone_home(hass: HomeAssistant) -> bool:
    """True when no persons are enabled, or at least one of them is home."""
    persons = household_persons(hass)
    if not persons:
        return True
    return any((st := hass.states.get(p)) is not None and st.state == "home" for p in persons)


# ── curtains that run the wrong way round ──────────────────────────────────

_COVER_SWAP = {
    "open_cover": "close_cover", "close_cover": "open_cover",
    "open": "closed", "closed": "open", "opening": "closing", "closing": "opening",
}


@callback
def inverted_covers(hass: HomeAssistant) -> set[str]:
    """Curtains marked as reversed in any room (open = closed)."""
    out: set[str] = set()
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        out.update(c for c in room.get(CONF_COVERS_INVERTED, []) or [] if c in (room.get(CONF_COVERS) or []))
    return out


def swap_cover(value: str) -> str:
    """open_cover ↔ close_cover, open ↔ closed, opening ↔ closing; others unchanged."""
    return _COVER_SWAP.get(value, value)
