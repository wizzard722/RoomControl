"""Announcements ("Omroepen"): one spoken message on the speakers of the house.

The speech service (tts.*) is a general setting (`announce_tts`; older
installs had it as `smoke_tts`). Every media player of a managed room takes
part, unless the room switched it off (room option `announce_off`: players
that don't). A room with linked persons (Aanwezigheid) is skipped while none
of them is home; a room without linked persons always takes part.

Used by smoke detectors, the doorbell (only rooms where someone is) and the
service `roomcontrol.announce` (message, optional areas).

Volume (general setting `volumes`: {"smoke" | "doorbell" | "announce": 0-100}):
when set, the speakers go to that volume for the message and back to their own
volume once they stopped playing (at most RESTORE_MAX seconds). Missing: the
speakers keep their volume.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import CONF_MEDIA_PLAYERS, DOMAIN
from .rooms import managed_areas, presence_allows, room_motion_sensors

_LOGGER = logging.getLogger(__name__)

SETTING_ANNOUNCE_TTS = "announce_tts"
SETTING_VOLUMES = "volumes"
VOLUME_KINDS = ("smoke", "doorbell", "announce")
RESTORE_MAX = 30  # s
RESTORE_START = 3  # s: give the speaker time to start playing
CONF_ANNOUNCE_OFF = "announce_off"
OCCUPIED_MINUTES = 10


def announce_tts(hass: HomeAssistant) -> str | None:
    """The speech service; the older smoke setting counts while there is no new one."""
    settings = hass.data.get(DOMAIN, {}).get("settings", {})
    value = settings[SETTING_ANNOUNCE_TTS] if SETTING_ANNOUNCE_TTS in settings else settings.get("smoke_tts")
    return value or None


def room_occupied(hass: HomeAssistant, room: dict[str, Any]) -> bool:
    """Someone is probably here: motion now or in the last minutes, or no sensors."""
    sensors = room_motion_sensors(room)
    if not sensors:
        return True
    now = dt_util.utcnow()
    return any(
        (st := hass.states.get(s)) is not None
        and (st.state in ("on", "detected") or now - st.last_changed <= timedelta(minutes=OCCUPIED_MINUTES))
        for s in sensors
    )


def announce_rooms(hass: HomeAssistant) -> list[str]:
    """Managed rooms that have media players (they get an Omroepen switch/notify)."""
    managed = managed_areas(hass)
    return [
        room["area_id"] for room in hass.data.get(DOMAIN, {}).get("rooms", [])
        if room.get("area_id") in managed and any(room.get(CONF_MEDIA_PLAYERS, []) or [])
    ]


def announce_players(
    hass: HomeAssistant, areas: list[str] | None = None, occupied_only: bool = False
) -> list[str]:
    """The media players a message goes to now."""
    managed = managed_areas(hass)
    players: list[str] = []
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        area = room.get("area_id")
        if area not in managed or (areas and area not in areas):
            continue
        if not presence_allows(hass, room):
            continue  # none of the room's persons is home
        if occupied_only and not room_occupied(hass, room):
            continue
        off = set(room.get(CONF_ANNOUNCE_OFF, []) or [])
        for player in room.get(CONF_MEDIA_PLAYERS, []) or []:
            if player and player not in off and player not in players:
                players.append(player)
    return players


def announce_volume(hass: HomeAssistant, kind: str) -> float | None:
    """Volume (0-1) for this kind of message; None: leave the speakers as they are."""
    value = (hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_VOLUMES) or {}).get(kind)
    if not isinstance(value, (int, float)):
        return None
    return min(100, max(0, value)) / 100


async def _async_restore_volumes(hass: HomeAssistant, before: dict[str, float]) -> None:
    """Once the speakers stopped playing (or after RESTORE_MAX s): their own volume back."""
    await asyncio.sleep(RESTORE_START)
    waited = RESTORE_START
    while waited < RESTORE_MAX and any(
        (st := hass.states.get(p)) is not None and st.state == "playing" for p in before
    ):
        await asyncio.sleep(1)
        waited += 1
    groups: dict[float, list[str]] = {}
    for player, level in before.items():
        groups.setdefault(level, []).append(player)
    for level, players in groups.items():
        try:
            await hass.services.async_call(
                "media_player", "volume_set", {ATTR_ENTITY_ID: players, "volume_level": level}, blocking=True
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Announce: restoring the volume of %s failed", players)


async def async_announce(
    hass: HomeAssistant, message: str, areas: list[str] | None = None, occupied_only: bool = False,
    kind: str = "announce",
) -> list[str]:
    """Speak `message` on the speakers that take part now (volume of `kind`). Returns them."""
    tts = announce_tts(hass)
    players = announce_players(hass, areas, occupied_only)
    if not tts or not players or not message:
        _LOGGER.debug("Announce skipped (tts=%s, players=%s)", tts, players)
        return []
    volume = announce_volume(hass, kind)
    if volume is not None:
        before = {
            p: float(level) for p in players
            if (st := hass.states.get(p)) is not None
            and isinstance(level := st.attributes.get("volume_level"), (int, float))
        }
        try:
            await hass.services.async_call(
                "media_player", "volume_set", {ATTR_ENTITY_ID: players, "volume_level": volume}, blocking=True
            )
        except Exception:  # noqa: BLE001 - a speaker without volume still speaks
            _LOGGER.exception("Announce: setting the volume of %s failed", players)
        if before:
            hass.async_create_task(_async_restore_volumes(hass, before))
    try:
        await hass.services.async_call(
            "tts", "speak",
            {ATTR_ENTITY_ID: tts, "media_player_entity_id": players, "message": message},
            blocking=True,
        )
    except Exception:  # noqa: BLE001 - a failing speaker must not break the caller
        _LOGGER.exception("Announce on %s failed", players)
        return []
    return players
