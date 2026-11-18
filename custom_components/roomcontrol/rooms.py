"""Room helpers shared by setup and the light platform."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant, callback

from .slots import hm_minutes
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
    CONF_MOTION_WINDOWS,
    DAYLIGHT_HIGH_ELEVATION,
    DAYLIGHT_LOW_ELEVATION,
    DAYLIGHT_MAX_KELVIN,
    DAYLIGHT_MIN_KELVIN,
    KELVIN_COLOR_MODES,
    CONF_PERSONS,
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
def motion_window(hass: HomeAssistant, sensor: str) -> tuple[int, int] | None:
    """(start, end) in minutes after midnight of the sensor's time window, set on
    the room the sensor belongs to; None = no window (always)."""
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        window = (room.get(CONF_MOTION_WINDOWS) or {}).get(sensor)
        if isinstance(window, dict) and sensor in room_motion_sensors(room):
            start, end = hm_minutes(window.get("start")), hm_minutes(window.get("end"))
            if start is not None and end is not None and start != end:
                return start, end
    return None


def in_window(window: tuple[int, int] | None, minutes: int) -> bool:
    """minutes (after midnight) inside the window; a window may cross midnight."""
    if window is None:
        return True
    start, end = window
    return start <= minutes < end if start < end else minutes >= start or minutes < end


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


# General setting "layout" (panel → Indeling): where each room is drawn per
# floor and how rooms adjoin. {"rooms": {area_id: {"x", "y", "w", "h"}},
# "links": [{"a": area_id, "b": area_id, "kind": "door" | "open" | "stairs",
# "sensor": binary_sensor (a door; none = a fictitious door)}],
# "landings": [area_id] (rooms with a landing; consecutive floors get stairs),
# "items": {entity_id: {"rx", "ry"}} (lamp/sensor place in its room, 0..1),
# "extra": {id: {"name", "floor"}} (rooms drawn only in the panel, not in Home
# Assistant), "stairs": {area_id: {"rx", "ry", "w", "h", "rot"}} (the stairs
# drawn in a landing)}. A room's "points" (optional) is its outline.
# A link works both ways and is information only (it switches nothing).
SETTING_LAYOUT = "layout"
LINK_KINDS = ("door", "open", "stairs")


@callback
def room_neighbours(hass: HomeAssistant, area_id: str) -> list[dict[str, str]]:
    """The rooms this one adjoins: [{"area_id", "kind"}] (from the layout)."""
    layout = hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_LAYOUT) or {}
    out: list[dict[str, str]] = []
    extra = layout.get("extra") or {}
    for link in layout.get("links", []) or []:
        if not isinstance(link, dict):
            continue
        a, b = link.get("a"), link.get("b")
        kind = link.get("kind") if link.get("kind") in LINK_KINDS else "door"
        other = b if a == area_id else a if b == area_id else None
        if other in extra:
            continue  # a room drawn only in the panel, not a Home Assistant area
        if other and other != area_id and all(o["area_id"] != other for o in out):
            item = {"area_id": other, "kind": kind}
            if kind == "door" and isinstance(link.get("sensor"), str) and link["sensor"]:
                item["sensor"] = link["sensor"]  # else a fictitious door (no sensor)
            out.append(item)
    # Landings ("overloop"): those of consecutive floors are joined by stairs.
    for other in _landing_neighbours(hass, layout.get("landings") or [], area_id):
        if all(o["area_id"] != other for o in out):
            out.append({"area_id": other, "kind": "stairs"})
    return out


def _landing_neighbours(hass: HomeAssistant, landings: list[str], area_id: str) -> list[str]:
    """Landings on the floor directly above and below, when area_id is a landing."""
    if area_id not in landings:
        return []
    from homeassistant.helpers import area_registry as ar, floor_registry as fr

    areas, floors = ar.async_get(hass), fr.async_get(hass)
    ordered = sorted(
        floors.async_list_floors(), key=lambda f: (f.level if f.level is not None else 0, f.name)
    )
    index = {f.floor_id: i for i, f in enumerate(ordered)}

    def floor_index(area: str) -> int | None:
        entry = areas.async_get_area(area)
        return index.get(entry.floor_id) if entry and entry.floor_id else None

    mine = floor_index(area_id)
    if mine is None:
        return []
    return [a for a in landings if a != area_id and (fi := floor_index(a)) is not None and abs(fi - mine) == 1]


@callback
def all_dim_rooms(hass: HomeAssistant) -> list[str]:
    """Rooms "Alles dim" acts on: configured rooms with lamps that are not hidden."""
    return [
        r["area_id"] for r in hass.data.get(DOMAIN, {}).get("rooms", [])
        if r.get("area_id") and r.get("lights") and not r.get("hidden")
    ]


@callback
def cover_state(hass: HomeAssistant, state: Any) -> str:
    """The curtain's state as it really is. "Reversed" only swaps the open and
    close commands; a curtain that reports a position reports its state the
    right way round. Without a position its reported state follows the
    (swapped) commands, so that one is swapped back."""
    if state.entity_id in inverted_covers(hass) and not isinstance(
        state.attributes.get("current_position"), (int, float)
    ):
        return swap_cover(state.state)
    return state.state


def swap_cover(value: str) -> str:
    """open_cover ↔ close_cover, open ↔ closed, opening ↔ closing; others unchanged."""
    return _COVER_SWAP.get(value, value)
