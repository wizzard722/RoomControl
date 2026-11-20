"""Keep the rooms' lamps in step with Home Assistant's areas.

A room's lamps are the ones the user added in the panel (room "lights", and
per light bundle "groups[].lights"). The panel only offers lamps of the
room's own area, so a lamp whose area changes in Home Assistant (the light
itself, or its device) no longer belongs to that room:

- it leaves the room and its light bundles;
- when its new area is a RoomControl room, it joins that room (outside any
  light bundle), keeping its own lamp settings;
- a lamp removed from Home Assistant leaves its room too;
- a lamp that gets a new entity ID keeps its place under the new ID.

Checked at start-up (a move made while RoomControl was not running) and on
every change in the entity and device registries.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import copy
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LampSync:
    def __init__(self, hass: HomeAssistant, save: Callable[[HomeAssistant, list[dict[str, Any]]], Awaitable[None]]) -> None:
        self.hass = hass
        self._save = save
        self._unsubs: list[CALLBACK_TYPE] = []
        self._pending: CALLBACK_TYPE | None = None
        self._removed: set[str] = set()
        self._renamed: dict[str, str] = {}

    @callback
    def start(self) -> None:
        self._unsubs.append(self.hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_entity))
        self._unsubs.append(self.hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, self._on_device))
        self._schedule()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        if self._pending:
            self._pending()
            self._pending = None

    @callback
    def _on_entity(self, event: Event) -> None:
        entity_id = event.data.get("entity_id") or ""
        if not entity_id.startswith("light."):
            return
        action = event.data.get("action")
        if action == "remove":
            self._removed.add(entity_id)
        elif action == "update":
            changes = event.data.get("changes") or {}
            if old := changes.get("entity_id"):
                self._renamed[old] = entity_id
                self._schedule()
            elif "area_id" in changes or "device_id" in changes:
                self._schedule()
            return
        self._schedule()

    @callback
    def _on_device(self, event: Event) -> None:
        if event.data.get("action") == "update" and "area_id" in (event.data.get("changes") or {}):
            self._schedule()

    @callback
    def _schedule(self) -> None:
        """Several changes at once (a device with many lamps) give one check."""
        if self._pending:
            self._pending()

        @callback
        def _run(_now: Any) -> None:
            self._pending = None
            self.hass.async_create_task(self.async_sync())

        self._pending = async_call_later(self.hass, 1, _run)

    def area_of(self, entity_id: str) -> tuple[bool, str | None]:
        """(known to the entity registry, the lamp's area: its own, else its device's)."""
        ent_reg = er.async_get(self.hass)
        entry = ent_reg.async_get(entity_id)
        if entry is None:
            return False, None
        if entry.area_id:
            return True, entry.area_id
        if entry.device_id and (device := dr.async_get(self.hass).async_get(entry.device_id)):
            return True, device.area_id
        return True, None

    async def async_sync(self) -> list[tuple[str, str, str | None]]:
        """Move lamps whose area changed. Returns [(lamp, from area, to area)]."""
        data = self.hass.data.get(DOMAIN, {})
        rooms: list[dict[str, Any]] = copy.deepcopy(data.get("rooms", []))
        removed, self._removed = self._removed, set()
        renamed, self._renamed = self._renamed, {}
        if renamed:
            for room in rooms:
                for light in room.get("lights", []) or []:
                    if isinstance(light, dict) and light.get("entity_id") in renamed:
                        light["entity_id"] = renamed[light["entity_id"]]
                for group in room.get("groups", []) or []:
                    if isinstance(group, dict):
                        group["lights"] = [renamed.get(e, e) for e in group.get("lights") or []]
        by_area = {r.get("area_id"): r for r in rooms if r.get("area_id")}
        moves: list[tuple[str, str, str | None]] = []
        for room in rooms:
            area = room.get("area_id")
            for light in list(room.get("lights", []) or []):
                lamp = light.get("entity_id") if isinstance(light, dict) else None
                if not lamp:
                    continue
                known, now = self.area_of(lamp)
                if not known:
                    # Not in the entity registry: only a lamp removed from Home
                    # Assistant leaves (a YAML light has no registry entry).
                    if lamp in removed and self.hass.states.get(lamp) is None:
                        moves.append((lamp, area, None))
                        self._take_out(room, lamp)
                    continue
                if now == area:
                    continue
                moves.append((lamp, area, now))
                self._take_out(room, lamp)
                target = by_area.get(now) if now else None
                if target is not None and not any(
                    isinstance(l, dict) and l.get("entity_id") == lamp for l in target.get("lights", []) or []
                ):
                    target.setdefault("lights", []).append(light)
        if moves or renamed:
            for old, new in renamed.items():
                _LOGGER.info("RoomControl: lamp %s is now %s", old, new)
            for lamp, src, dst in moves:
                _LOGGER.info("RoomControl: lamp %s left room %s%s", lamp, src, f" for room {dst}" if dst else "")
            await self._save(self.hass, rooms)
        return moves

    @staticmethod
    def _take_out(room: dict[str, Any], lamp: str) -> None:
        room["lights"] = [l for l in room.get("lights", []) or [] if not (isinstance(l, dict) and l.get("entity_id") == lamp)]
        for group in room.get("groups", []) or []:
            if isinstance(group, dict) and lamp in (group.get("lights") or []):
                group["lights"] = [e for e in group["lights"] if e != lamp]
