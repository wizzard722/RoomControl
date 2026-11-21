"""Fan platform: the room's fans (own and shared) as one fan on the room's device."""
from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .entity_ids import with_roomcontrol_ids
from .const import CONF_FANS_NAME, DEFAULT_FANS_NAME, DOMAIN, SIGNAL_CONFIG_UPDATED
from .rooms import managed_areas, room_fans, stored_room


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_fans"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Keep one fan entity per room that has fans."""
    async_add_entities = with_roomcontrol_ids(hass, "fan", async_add_entities)
    entities: dict[str, RoomFan] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {
            room["area_id"]
            for room in hass.data.get(DOMAIN, {}).get("rooms", [])
            if room.get("area_id") in areas and room_fans(hass, room["area_id"])
        }
        new = [RoomFan(a) for a in wanted - entities.keys()]
        for entity in new:
            entities[entity.area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(entities.keys() - wanted):
            del entities[area_id]
            if entity_id := ent_reg.async_get_entity_id("fan", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class RoomFan(FanEntity):
    """All fans of a room together: on/off and speed."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self._attr_unique_id = _unique_id(area_id)
        self._members: list[str] = []
        self._unsub: CALLBACK_TYPE | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    @property
    def name(self) -> str:
        room = stored_room(self.hass, self.area_id) or {}
        return (room.get(CONF_FANS_NAME) or "").strip() or DEFAULT_FANS_NAME

    @callback
    def _refresh(self, *_: Any) -> None:
        members = room_fans(self.hass, self.area_id)  # own + shared with other rooms
        if members != self._members:
            if self._unsub:
                self._unsub()
            self._members = members
            self._unsub = async_track_state_change_event(self.hass, members, self._refresh) if members else None
        states = [s for f in self._members if (s := self.hass.states.get(f)) is not None]
        on = [s for s in states if s.state == STATE_ON]
        speeds = [p for s in on if isinstance(p := s.attributes.get("percentage"), (int, float))]
        self._attr_available = bool(states)
        self._attr_is_on = bool(on)
        self._attr_percentage = round(sum(speeds) / len(speeds)) if speeds else (0 if not on else None)
        self._attr_extra_state_attributes = {ATTR_ENTITY_ID: list(self._members), "roomcontrol_area": self.area_id}
        if self.entity_id:
            self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        return self._attr_is_on

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _call(self, service: str, **data: Any) -> None:
        if self._members:
            await self.hass.services.async_call(
                "fan", service, {ATTR_ENTITY_ID: self._members, **data}, blocking=True
            )

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        if percentage is not None:
            await self._call("set_percentage", percentage=percentage)
        else:
            await self._call("turn_on")

    async def _off(self) -> None:
        """Off; with the room option "fan_off_min" (off = 1%) to 1% instead."""
        if (stored_room(self.hass, self.area_id) or {}).get("fan_off_min"):
            await self._call("set_percentage", percentage=1)
        else:
            await self._call("turn_off")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._off()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self._off()
        else:
            await self._call("set_percentage", percentage=percentage)
