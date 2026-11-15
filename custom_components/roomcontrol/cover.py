"""Cover platform: the room's curtains as one cover, plus one per curtain group.

They hang on the room's device, so they can be put on any dashboard.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_COVER_GROUPS,
    CONF_COVERS,
    CONF_COVERS_NAME,
    DEFAULT_COVERS_NAME,
    DOMAIN,
    SIGNAL_CONFIG_UPDATED,
)
from .control import rc_call
from .rooms import inverted_covers, managed_areas, stored_room, swap_cover

ALL = "all"  # group id of the "all curtains of the room" cover


def _unique_id(area_id: str, group_id: str) -> str:
    return f"{DOMAIN}_{area_id}_covers" if group_id == ALL else f"{DOMAIN}_{area_id}_covergroup_{group_id}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Keep one cover per room with curtains and one per curtain group."""
    entities: dict[tuple[str, str], RoomCover] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted: set[tuple[str, str]] = set()
        for room in hass.data.get(DOMAIN, {}).get("rooms", []):
            area_id = room.get("area_id")
            if area_id not in areas or not room.get(CONF_COVERS):
                continue
            wanted.add((area_id, ALL))
            for group in room.get(CONF_COVER_GROUPS, []) or []:
                if group.get("id"):
                    wanted.add((area_id, group["id"]))
        new = [RoomCover(a, g) for (a, g) in wanted - entities.keys()]
        for entity in new:
            entities[(entity.area_id, entity.group_id)] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key in list(entities.keys() - wanted):
            del entities[key]
            if entity_id := ent_reg.async_get_entity_id("cover", DOMAIN, _unique_id(*key)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))


class RoomCover(CoverEntity):
    """A group of the room's curtains (all of them, or one curtain group)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, area_id: str, group_id: str) -> None:
        self.area_id = area_id
        self.group_id = group_id
        self._attr_unique_id = _unique_id(area_id, group_id)
        self._attr_icon = "mdi:curtains"
        self._members: list[str] = []
        self._unsub: CALLBACK_TYPE | None = None

    def _room(self) -> dict[str, Any]:
        return stored_room(self.hass, self.area_id) or {}

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    def _group(self) -> tuple[int, dict[str, Any]] | None:
        for index, group in enumerate(self._room().get(CONF_COVER_GROUPS, []) or []):
            if group.get("id") == self.group_id:
                return index, group
        return None

    @property
    def name(self) -> str:
        room = self._room()
        if self.group_id == ALL:
            return (room.get(CONF_COVERS_NAME) or "").strip() or DEFAULT_COVERS_NAME
        found = self._group()
        if not found:
            return self.group_id
        index, group = found
        return (group.get("name") or "").strip() or f"Groep {index + 1}"

    @callback
    def _refresh(self, *_: Any) -> None:
        room = self._room()
        own = [c for c in room.get(CONF_COVERS, []) or [] if c]
        if self.group_id == ALL:
            members = own
        else:
            found = self._group()
            members = [c for c in (found[1].get("covers", []) if found else []) if c in own]
        if members != self._members:
            if self._unsub:
                self._unsub()
            self._members = members
            self._unsub = async_track_state_change_event(self.hass, members, self._refresh) if members else None

        states = [s for c in self._members if (s := self.hass.states.get(c)) is not None]
        self._attr_available = bool(states)
        # Reversed curtains: their reported state is the other way round.
        reversed_ = inverted_covers(self.hass)
        logical = [
            (swap_cover(s.state) if s.entity_id in reversed_ else s.state, s) for s in states
        ]
        known = [st for st, _ in logical if st in ("open", "closed", "opening", "closing")]
        self._attr_is_opening = any(st == "opening" for st in known)
        self._attr_is_closing = any(st == "closing" for st in known)
        self._attr_is_closed = bool(known) and all(st == "closed" for st in known) if known else None
        positions = [
            100 - p if s.entity_id in reversed_ else p
            for s in states if isinstance(p := s.attributes.get("current_position"), (int, float))
        ]
        self._attr_current_cover_position = round(sum(positions) / len(positions)) if positions else None
        features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        if states and all(
            int(s.attributes.get("supported_features", 0)) & CoverEntityFeature.SET_POSITION for s in states
        ):
            features |= CoverEntityFeature.SET_POSITION
        self._attr_supported_features = features
        self._attr_extra_state_attributes = {
            ATTR_ENTITY_ID: list(self._members),
            "roomcontrol_area": self.area_id,
            "roomcontrol_cover_group": self.group_id,
        }
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _call(self, service: str, **data: Any) -> None:
        if self._members:
            await rc_call(self.hass,
                "cover", service, {ATTR_ENTITY_ID: self._members, **data}, blocking=True
            )

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._call("open_cover")

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._call("close_cover")

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._call("stop_cover")

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self._call("set_cover_position", position=kwargs[ATTR_POSITION])
