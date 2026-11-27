"""Schemakeuze: the heating schedule as a select, on the room's device (a room
with its own selector) or on the General device (the house's selector).

The select is a view of the selector helper (input_number / input_boolean)
that RoomMind reads: RoomMind only follows input_number and input_boolean,
so the helper stays the source and the select sets it. Options are the
schedules' names (heating.schedule_name), made unique.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, GENERAL_DEVICE, SIGNAL_CONFIG_UPDATED
from .entity_ids import with_roomcontrol_ids
from .heating import async_set_selector, general_cfg, heating_cfg, schedule_name, selector_range, selector_value

HOUSE = "__house__"


def _unique_id(key: str) -> str:
    return f"{DOMAIN}_general_schedule" if key == HOUSE else f"{DOMAIN}_{key}_schedule"


def schedule_selectors(hass: HomeAssistant) -> dict[str, str]:
    """area (or HOUSE) → the selector a Schemakeuze select shows."""
    out = {}
    if sel := general_cfg(hass).get("selector"):
        out[HOUSE] = sel
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        h = heating_cfg(room)
        if h.get("scope", "room") == "room" and h.get("selector") and room.get("area_id"):
            out[room["area_id"]] = h["selector"]
    return out


def schedule_options(hass: HomeAssistant, area: str | None, selector: str) -> list[tuple[int, str]]:
    """[(value, unique name), ...] for the selector's range."""
    lo, hi = selector_range(hass, selector)
    out, seen = [], set()
    for v in range(max(1, lo), hi + 1):
        name = schedule_name(hass, area, v)
        if name in seen:
            name = f"{v} · {name}"
        seen.add(name)
        out.append((v, name))
    return out


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities = with_roomcontrol_ids(hass, "select", async_add_entities)
    entities: dict[str, ScheduleSelect] = {}

    @callback
    def _sync(*_: Any) -> None:
        wanted = set(schedule_selectors(hass))
        new = [ScheduleSelect(k) for k in wanted - entities.keys()]
        for entity in new:
            entities[entity.key] = entity
        if new:
            async_add_entities(new)
        reg = er.async_get(hass)
        for key in list(entities.keys() - wanted):
            del entities[key]
            if entity_id := reg.async_get_entity_id("select", DOMAIN, _unique_id(key)):
                reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class ScheduleSelect(SelectEntity):
    """Schemakeuze: which heating schedule is on (sets the selector helper)."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:calendar-clock"
    _attr_name = "Schemakeuze"

    def __init__(self, key: str) -> None:
        self.key = key
        self._attr_unique_id = _unique_id(key)
        self._attr_device_info = (DeviceInfo(identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl")
                                  if key == HOUSE else DeviceInfo(identifiers={(DOMAIN, key)}))
        self._unsub: CALLBACK_TYPE | None = None
        self._watching: tuple[str, ...] = ()
        self._options: list[tuple[int, str]] = []

    @property
    def _area(self) -> str | None:
        return None if self.key == HOUSE else self.key

    @property
    def _selector(self) -> str | None:
        return schedule_selectors(self.hass).get(self.key)

    @callback
    def _refresh(self, *_: Any) -> None:
        sel = self._selector
        room = next((r for r in self.hass.data.get(DOMAIN, {}).get("rooms", []) if r.get("area_id") == self._area), None)
        watch = tuple(x for x in [sel, *(heating_cfg(room).get("schedules") or [])] if x)
        if watch != self._watching:
            if self._unsub:
                self._unsub()
            self._watching = watch
            self._unsub = async_track_state_change_event(self.hass, list(watch), self._refresh) if watch else None
        self._options = schedule_options(self.hass, self._area, sel) if sel else []
        value = selector_value(self.hass, sel)
        self._attr_available = bool(sel) and self.hass.states.get(sel) is not None
        self._attr_options = [n for _, n in self._options]
        self._attr_current_option = next((n for v, n in self._options if v == value), None)
        self._attr_extra_state_attributes = {"selector": sel, "value": value}
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def async_select_option(self, option: str) -> None:
        sel = self._selector
        value = next((v for v, n in self._options if n == option), None)
        if sel and value is not None:
            await async_set_selector(self.hass, sel, value)
