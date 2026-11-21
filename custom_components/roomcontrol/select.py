"""The "Vakantie" select on the General device: off, at home or elsewhere.

It mirrors (and sets) the Vakantie switch (switch.py): choosing "home" or
"away" switches vacation on with that kind, kept until vacation ends;
"off" switches it off.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GENERAL_DEVICE, SIGNAL_VACATION
from .entity_ids import with_roomcontrol_ids

OPTIONS = ["off", "home", "away"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities = with_roomcontrol_ids(hass, "select", async_add_entities)
    async_add_entities([VacationSelect()])


class VacationSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:palm-tree"
    _attr_translation_key = "vacation"  # "Vakantie" / "Vacation"
    _rc_id_name = "Vakantie soort"  # entity ID: select.roomcontrol_generiek_vakantie_soort
    _attr_unique_id = f"{DOMAIN}_vacation_kind"
    _attr_options = OPTIONS

    def __init__(self) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_VACATION, self._changed))

    @callback
    def _changed(self) -> None:
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        value = self.hass.data.get(DOMAIN, {}).get("vacation")
        return value if value in ("home", "away") else ("home" if value else "off")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"roomcontrol_vacation_kind": True}

    async def async_select_option(self, option: str) -> None:
        switch = self.hass.data.get(DOMAIN, {}).get("vacation_switch")
        if switch is not None:
            switch.set_mode(option)
