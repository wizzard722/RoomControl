"""Lock platform: the room's locks, on the room's device ("Bediening").

Each RoomControl lock follows one real lock; locking and opening go through
it. The panel asks before opening when the lock's "confirm_open" is on; Home
Assistant itself has no such question, so here it opens straight away.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED
from .rooms import managed_areas, room_locks


def _unique_id(area_id: str, entity_id: str) -> str:
    return f"{DOMAIN}_{area_id}_lock_{entity_id.partition('.')[2]}"


def wanted_locks(hass: HomeAssistant) -> set[tuple[str, str]]:
    """(area_id, lock entity id) for every lock of every managed room."""
    areas = managed_areas(hass)
    return {
        (room["area_id"], lock["entity_id"])
        for room in hass.data.get(DOMAIN, {}).get("rooms", [])
        if room.get("area_id") in areas
        for lock in room_locks(room)
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Keep one RoomControl lock per configured lock."""
    entities: dict[tuple[str, str], RoomLock] = {}

    @callback
    def _sync(*_: Any) -> None:
        wanted = wanted_locks(hass)
        new = [RoomLock(a, e) for (a, e) in wanted - entities.keys()]
        for entity in new:
            entities[(entity.area_id, entity.target)] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key in list(entities.keys() - wanted):
            del entities[key]
            if entity_id := ent_reg.async_get_entity_id("lock", DOMAIN, _unique_id(*key)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class RoomLock(LockEntity):
    """One of the room's locks."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, area_id: str, target: str) -> None:
        self.area_id = area_id
        self.target = target
        self._attr_unique_id = _unique_id(area_id, target)
        self._unsub: CALLBACK_TYPE | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    @property
    def name(self) -> str:
        state = self.hass.states.get(self.target) if self.hass else None
        return (state.attributes.get("friendly_name") if state else None) or self.target

    @callback
    def _refresh(self, *_: Any) -> None:
        state = self.hass.states.get(self.target)
        self._attr_available = state is not None and state.state not in ("unavailable", "unknown")
        current = state.state if state is not None else None
        self._attr_is_locked = current == "locked"
        self._attr_is_locking = current == "locking"
        self._attr_is_unlocking = current == "unlocking"
        self._attr_is_jammed = current == "jammed"
        self._attr_is_open = current == "open"
        self._attr_is_opening = current == "opening"
        features = int(state.attributes.get("supported_features", 0)) if state is not None else 0
        self._attr_supported_features = LockEntityFeature(features & LockEntityFeature.OPEN)
        self._attr_extra_state_attributes = {
            ATTR_ENTITY_ID: [self.target],
            "roomcontrol_area": self.area_id,
        }
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._unsub = async_track_state_change_event(self.hass, [self.target], self._refresh)
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _call(self, service: str, **data: Any) -> None:
        await self.hass.services.async_call("lock", service, {ATTR_ENTITY_ID: self.target, **data}, blocking=True)

    async def async_lock(self, **kwargs: Any) -> None:
        await self._call("lock", **kwargs)

    async def async_unlock(self, **kwargs: Any) -> None:
        await self._call("unlock", **kwargs)

    async def async_open(self, **kwargs: Any) -> None:
        await self._call("open", **kwargs)
