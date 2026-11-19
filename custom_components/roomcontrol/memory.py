"""RoomControl's working memory, kept across a restart of Home Assistant.

Rooms (Dim, manual control, grace period, Home later, what happened, …),
smoke ("until All safe"), the doorbell's screen message and full control
each register a provider that returns their state. The memory collects them
every few minutes and when Home Assistant stops, and saves them to
.storage/roomcontrol.memory; at the next start each part reads its own
section back with `get`.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.memory"
SAVE_INTERVAL = timedelta(minutes=5)


class Memory:
    """Sections of state, each filled by a provider and read back at startup."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        self.data: dict[str, Any] = {}
        self._providers: dict[str, Callable[[], Any]] = {}
        self._unsubs: list[CALLBACK_TYPE] = []

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        self.data = stored if isinstance(stored, dict) else {}

    def get(self, key: str) -> Any:
        """What was saved for `key` before the restart (None: nothing)."""
        return self.data.get(key)

    @callback
    def register(self, key: str, provider: Callable[[], Any]) -> CALLBACK_TYPE:
        """`provider()` returns the state to keep for `key` (None: forget it)."""
        self._providers[key] = provider

        @callback
        def _unregister() -> None:
            if self._providers.get(key) is provider:
                # Keep its last state (an entity that is reloaded reads it back).
                self._collect_one(key, provider)
                del self._providers[key]

        return _unregister

    @callback
    def changed(self) -> None:
        """Something important changed: save soon."""
        self._store.async_delay_save(self._collect, 10)

    def _collect_one(self, key: str, provider: Callable[[], Any]) -> None:
        try:
            value = provider()
        except Exception:  # noqa: BLE001 - one broken part must not lose the rest
            _LOGGER.exception("RoomControl memory: could not collect %s", key)
            return
        if value is None:
            self.data.pop(key, None)
        else:
            self.data[key] = value

    def _collect(self) -> dict[str, Any]:
        for key, provider in list(self._providers.items()):
            self._collect_one(key, provider)
        return self.data

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, SAVE_INTERVAL))
        self._unsubs.append(self.hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, self._on_stop))

    @callback
    def _tick(self, _now: Any = None) -> None:
        self._store.async_delay_save(self._collect, 1)

    async def _on_stop(self, _event: Event) -> None:
        await self.async_save()

    async def async_save(self) -> None:
        await self._store.async_save(self._collect())

    async def async_stop(self) -> None:
        """Integration unloads: save, then stop."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        await self.async_save()


@callback
def memory(hass: HomeAssistant) -> Memory | None:
    return hass.data.get(DOMAIN, {}).get("memory")
