"""Button platform: "stop" for every alarm clock and "Alles op slot" for rooms
with several locks, on the room's device.

There is no snooze button: an alarm clock goes one step brighter each
interval by itself. Snooze buttons of older versions are removed."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .clocks import SIGNAL_CLOCKS_UPDATED, clock_key, room_clocks
from .entity_ids import with_roomcontrol_ids
from .const import DOMAIN, SIGNAL_CONFIG_UPDATED
from .rooms import managed_areas

ACTIONS = ("stop",)
ACTION_NAMES = {"snooze": "sluimeren", "stop": "stoppen"}
ACTION_ICONS = {"snooze": "mdi:alarm-snooze", "stop": "mdi:alarm-off"}


def _unique_id(key: str, action: str) -> str:
    return f"{DOMAIN}_clock_{key.replace(':', '_')}_{action}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Keep a stop button per alarm clock (and remove old snooze buttons)."""
    async_add_entities = with_roomcontrol_ids(hass, "button", async_add_entities)
    entities: dict[tuple[str, str], ClockButton] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {
            (clock_key(area_id, clock["id"]), action)
            for area_id, clock in room_clocks(hass) if area_id in areas
            for action in ACTIONS
        }
        new = [ClockButton(key, action) for key, action in wanted - entities.keys()]
        for entity in new:
            entities[(entity.key, entity.action)] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key, action in list(entities.keys() - wanted):
            del entities[(key, action)]
            if entity_id := ent_reg.async_get_entity_id("button", DOMAIN, _unique_id(key, action)):
                ent_reg.async_remove(entity_id)

    # Snooze buttons from older versions: away from the devices.
    ent_reg = er.async_get(hass)
    for reg_entry in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if reg_entry.domain == "button" and reg_entry.unique_id.endswith("_snooze"):
            ent_reg.async_remove(reg_entry.entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))

    # "Alles op slot" for rooms with more than one lock.
    lock_buttons: dict[str, LockAllButton] = {}

    @callback
    def _sync_locks(*_: Any) -> None:
        from .lock import wanted_locks

        count: dict[str, int] = {}
        for area_id, _entity in wanted_locks(hass):
            count[area_id] = count.get(area_id, 0) + 1
        wanted = {a for a, n in count.items() if n > 1}
        new = [LockAllButton(a) for a in wanted - lock_buttons.keys()]
        for entity in new:
            lock_buttons[entity.area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(lock_buttons.keys() - wanted):
            del lock_buttons[area_id]
            if entity_id := ent_reg.async_get_entity_id("button", DOMAIN, _lock_all_unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync_locks()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_locks))


def _lock_all_unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_lock_all"


class LockAllButton(ButtonEntity):
    """Lock every lock of the room."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "Alles op slot"
    _attr_icon = "mdi:lock-check"

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self._attr_unique_id = _lock_all_unique_id(area_id)

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    async def async_press(self) -> None:
        if (manager := self.hass.data.get(DOMAIN, {}).get("locks")) is not None:
            await manager.lock_room(self.area_id)


class ClockButton(ButtonEntity):
    """Stop one alarm clock."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, key: str, action: str) -> None:
        self.key = key
        self.action = action
        area_id = key.partition(":")[0]
        self._attr_unique_id = _unique_id(key, action)
        self._area_id = area_id
        self._attr_icon = ACTION_ICONS[action]

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self._area_id)})

    def _manager(self) -> Any:
        return self.hass.data.get(DOMAIN, {}).get("clocks")

    @property
    def name(self) -> str:
        manager = self._manager()
        found = manager.find(self.key) if manager else None
        label = ((found[2].get("name") or "").strip() or found[2].get("time", "")) if found else ""
        return f"Wekker {label} {ACTION_NAMES[self.action]}".strip()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Whether pressing does something now (the clock is going off or snoozing)."""
        manager = self._manager()
        state = manager.states.get(self.key) if manager else None
        return {"active": bool(state and state.active)}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CLOCKS_UPDATED, self.async_write_ha_state))

    async def async_press(self) -> None:
        manager = self._manager()
        if manager is None:
            return
        await manager.stop(self.key)
