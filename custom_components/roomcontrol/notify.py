"""Notify platform: "Omroepen" (announcements) as notify entities.

One on the General device (the whole house) and one per room with media
players (only that room). Sending a message speaks it on the speakers that
take part now (see announce.py); the title is not spoken.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .announce import announce_rooms, async_announce
from .entity_ids import with_roomcontrol_ids
from .const import DOMAIN, GENERAL_DEVICE, SIGNAL_CONFIG_UPDATED


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_announce_notify"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities = with_roomcontrol_ids(hass, "notify", async_add_entities)
    async_add_entities([AnnounceNotify(None)])
    rooms: dict[str, AnnounceNotify] = {}

    @callback
    def _sync(*_: Any) -> None:
        wanted = set(announce_rooms(hass))
        new = [AnnounceNotify(a) for a in wanted - rooms.keys()]
        for entity in new:
            rooms[entity.area_id] = entity  # type: ignore[index]
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(rooms.keys() - wanted):
            del rooms[area_id]
            if entity_id := ent_reg.async_get_entity_id("notify", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class AnnounceNotify(NotifyEntity):
    """Speak a message on the house's (or one room's) speakers."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bullhorn"
    _attr_name = "Omroepen"

    def __init__(self, area_id: str | None) -> None:
        self.area_id = area_id
        self._attr_unique_id = _unique_id(area_id or GENERAL_DEVICE)
        if area_id is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
            )
        else:
            self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, area_id)})

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        await async_announce(self.hass, message, [self.area_id] if self.area_id else None)
