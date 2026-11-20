"""Sensor platform: per room with curtains, the curtain state RoomControl knows;
and on the General device "Auto laden", the car's charging power (energy.py).

It hangs on the room's device (Sensors) and shows open, closed or partly
open from what RoomControl remembers (see covers_known), not from the
curtain's own, often wrong, state.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_COVERS, DOMAIN, GENERAL_DEVICE, SIGNAL_CONFIG_UPDATED
from .energy import SIGNAL_ENERGY
from .covers_known import CLOSED, OPEN, PARTLY, SIGNAL_COVERS_KNOWN, known_covers
from .entity_ids import with_roomcontrol_ids
from .rooms import managed_areas, stored_room


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_covers_state"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """One "Curtains status" sensor per room with curtains."""
    async_add_entities = with_roomcontrol_ids(hass, "sensor", async_add_entities)
    entities: dict[str, CoversStateSensor] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {
            r["area_id"] for r in hass.data.get(DOMAIN, {}).get("rooms", [])
            if r.get("area_id") in areas and r.get(CONF_COVERS)
        }
        new = [CoversStateSensor(a) for a in wanted - entities.keys()]
        for entity in new:
            entities[entity.area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(entities.keys() - wanted):
            del entities[area_id]
            if entity_id := ent_reg.async_get_entity_id("sensor", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))
    # "Auto laden" on the General device: is the car charging, and how fast.
    async_add_entities([EvChargingSensor()])


class CoversStateSensor(SensorEntity):
    """Open / closed / partly open: the room's curtains as RoomControl knows them."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "covers_state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [OPEN, CLOSED, PARTLY]

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
        return {OPEN: "mdi:curtains", CLOSED: "mdi:curtains-closed"}.get(self.native_value or "", "mdi:curtains")

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
        self._attr_native_value = known["state"] if known else None
        self._attr_extra_state_attributes = {
            "position": known["position"] if known else None,
            "roomcontrol_area": self.area_id,
            "roomcontrol_covers": known["covers"] if known else {},
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


class EvChargingSensor(SensorEntity):
    """The car's charging power (kW, 0 when not charging) on the General
    device, with the charging details as attributes (see energy.py)."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Auto laden"
    _attr_unique_id = f"{DOMAIN}_ev_charging"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_suggested_display_precision = 2

    def __init__(self) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_ENERGY, self._refresh))
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))
        self._refresh()

    def _car(self) -> dict[str, Any] | None:
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        return (energy.status().get("car") if energy is not None else None) or None

    @callback
    def _refresh(self, *_: Any) -> None:
        car = self._car()
        self._attr_available = car is not None
        self._attr_native_value = (car.get("kw") or 0.0) if car else None
        self._attr_icon = "mdi:car-electric" if car and car.get("charging") else "mdi:car"
        self._attr_extra_state_attributes = {} if not car else {
            "charging": car.get("charging"),
            "car": car.get("name") or None,
            "battery_level": car.get("soc"),
            "battery_kwh": car.get("kwh"),
            "battery_size_kwh": car.get("battery_kwh"),
            "full_at": car.get("full_at"),
            "charging_since": car.get("since"),
            "charged_kwh": car.get("charged_kwh"),
            "estimate_kw": car.get("estimate_kw"),
            "from_car": car.get("from_sensor"),
            "plugged_in": car.get("plugged"),
            "room": car.get("room"),
            "phase": car.get("phase"),
        }
        if self.hass is not None and self.entity_id:
            self.async_write_ha_state()
