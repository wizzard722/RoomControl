"""Binary sensor platform: per room with curtains, "Opening" (open / closed).

It hangs on the room's device (Sensors; Home Assistant names it after its
device class: "Opening", in Dutch "Openen") and is on when, as RoomControl
knows it (see covers_known), any of the room's curtains is open — partly
open counts as open. The curtains' own state, which is often wrong, is not
used.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_COVERS, DOMAIN, SIGNAL_CONFIG_UPDATED
from .covers_known import CLOSED, SIGNAL_COVERS_KNOWN, known_covers
from homeassistant.util import slugify

from .entity_ids import with_roomcontrol_ids
from .rooms import managed_areas, stored_room


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_covers_opening"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """One "Opening" binary sensor per room with curtains."""
    async_add_entities = with_roomcontrol_ids(hass, "binary_sensor", async_add_entities)
    entities: dict[str, CoversOpenSensor] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {
            r["area_id"] for r in hass.data.get(DOMAIN, {}).get("rooms", [])
            if r.get("area_id") in areas and r.get(CONF_COVERS)
        }
        new = [CoversOpenSensor(a) for a in wanted - entities.keys()]
        area_reg = ar.async_get(hass)
        for entity in new:
            entities[entity.area_id] = entity
            area = area_reg.async_get_area(entity.area_id)
            # Its name comes from the device class, so give the ID a word for it.
            entity.entity_id = f"binary_sensor.{slugify(f'{DOMAIN} {area.name if area else entity.area_id} opening')}"
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(entities.keys() - wanted):
            del entities[area_id]
            if entity_id := ent_reg.async_get_entity_id("binary_sensor", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class CoversOpenSensor(BinarySensorEntity):
    """On (open) when RoomControl knows one of the room's curtains is open."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.OPENING  # named "Opening" / "Openen" by Home Assistant

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self._attr_unique_id = _unique_id(area_id)
        self._members: list[str] = []
        self._unsub: CALLBACK_TYPE | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    @property
    def icon(self) -> str:
        return "mdi:curtains" if self.is_on else "mdi:curtains-closed"

    @callback
    def _refresh(self, *_: Any) -> None:
        room = stored_room(self.hass, self.area_id) or {}
        members = [c for c in room.get(CONF_COVERS, []) or [] if c]
        if members != self._members:
            if self._unsub:
                self._unsub()
            self._members = members
            # Curtains that were never commanded follow the device until then.
            self._unsub = async_track_state_change_event(self.hass, members, self._refresh) if members else None
        known = known_covers(self.hass, self._members)
        self._attr_available = known is not None
        self._attr_is_on = known["state"] != CLOSED if known else None
        self._attr_extra_state_attributes = {
            "state": known["state"] if known else None,  # open / closed / partly_open
            "position": known["position"] if known else None,
            "roomcontrol_area": self.area_id,
        }
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_COVERS_KNOWN, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
