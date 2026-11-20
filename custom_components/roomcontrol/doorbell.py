"""Doorbells per room (room option `doorbell`), e.g. a UniFi Protect G4 Doorbell.

Room option:
    {"entity": event.* (event_type "ring") or binary_sensor.* (off → on),
     "camera": camera.* (optional: still image in the notification),
     "pause_media": bool (default yes), "announce": bool (default no),
     "notify": bool (default yes),
     "quiet": {"from": "HH:MM", "to": "HH:MM"} (optional),
     "away_message": {"entity": select.* / text.*, "value": str} (optional)}

On a ring: media that plays in rooms where someone is (motion in the last
minutes, or rooms without motion sensors) is paused; with "announce"
the announcement speakers of those rooms (see announce.py) say so; a notification (with the camera image) and the
event `roomcontrol_doorbell`. During the quiet hours only the notification.
RoomControl never switches lamps for the doorbell.

"away_message": while nobody is home, the doorbell's screen shows this
message; once someone is home again, the previous one comes back.
"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .texts import text
from .const import CONF_MEDIA_PLAYERS, DOMAIN, SIGNAL_CONFIG_UPDATED
from .rooms import anyone_home, household_persons, managed_areas, presence_allows
from .slots import hm_minutes
from .smoke import smoke_active
from .announce import async_announce, room_occupied
from .nspanel import nspanel_message

_LOGGER = logging.getLogger(__name__)

CONF_DOORBELL = "doorbell"
RING_DEBOUNCE = timedelta(seconds=10)
PLAYING = ("playing",)


def in_quiet(quiet: dict[str, Any] | None, minutes: int) -> bool:
    """Is `minutes` after midnight inside the quiet hours (may cross midnight)?"""
    if not quiet:
        return False
    start, end = hm_minutes(quiet.get("from")), hm_minutes(quiet.get("to"))
    if start is None or end is None or start == end:
        return False
    return start <= minutes < end if start < end else minutes >= start or minutes < end


class DoorbellManager:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsubs: list[CALLBACK_TYPE] = []
        self._unsub_bells: CALLBACK_TYPE | None = None
        self._unsub_persons: CALLBACK_TYPE | None = None
        self._tracked: tuple[str, ...] = ()
        self._persons: tuple[str, ...] = ()
        self._last_ring: dict[str, Any] = {}
        # Screen entity → message it showed before the away message.
        self._saved_message: dict[str, str] = {}
        self._away_shown = False

    # ── config ─────────────────────────────────────────────────────────────

    def _bells(self) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """(room, doorbell config) of every managed room with a doorbell."""
        areas = managed_areas(self.hass)
        return [
            (room, bell) for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            if room.get("area_id") in areas
            and isinstance(bell := room.get(CONF_DOORBELL), dict) and bell.get("entity")
        ]

    def _memory_data(self) -> dict[str, Any] | None:
        """The away message shown and the messages to put back (see memory.py)."""
        if not self._away_shown and not self._saved_message:
            return None
        return {"away_shown": self._away_shown, "saved_message": dict(self._saved_message)}

    @callback
    def start(self) -> None:
        if (mem := self.hass.data.get(DOMAIN, {}).get("memory")) is not None:
            data = mem.get("doorbell")
            if isinstance(data, dict):
                # Away message still on the screen from before the restart: when
                # someone comes home, the earlier message goes back.
                self._away_shown = bool(data.get("away_shown"))
                self._saved_message = {
                    k: v for k, v in (data.get("saved_message") or {}).items() if isinstance(v, str)
                }
            self._unsubs.append(mem.register("doorbell", self._memory_data))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._sync()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for name in ("_unsub_bells", "_unsub_persons"):
            if (unsub := getattr(self, name)) is not None:
                unsub()
                setattr(self, name, None)

    @callback
    def _sync(self, *_: Any) -> None:
        ids = tuple(sorted({bell["entity"] for _room, bell in self._bells()}))
        if ids != self._tracked:
            if self._unsub_bells:
                self._unsub_bells()
                self._unsub_bells = None
            self._tracked = ids
            if ids:
                self._unsub_bells = async_track_state_change_event(self.hass, list(ids), self._on_bell)
        persons = tuple(household_persons(self.hass))
        if persons != self._persons:
            if self._unsub_persons:
                self._unsub_persons()
                self._unsub_persons = None
            self._persons = persons
            if persons:
                self._unsub_persons = async_track_state_change_event(self.hass, list(persons), self._on_presence)
        self._on_presence()

    # ── ringing ────────────────────────────────────────────────────────────

    @staticmethod
    def _is_ring(old: Any, new: Any) -> bool:
        if new is None or new.state in ("unavailable", "unknown"):
            return False
        if new.entity_id.startswith("event."):
            # The state is the time of the last event. Coming back from
            # "unavailable" (restart, network) is not a ring; "unknown" → a
            # time is (the very first ring).
            if old is None or old.state == "unavailable" or old.state == new.state:
                return False
            kind = new.attributes.get("event_type")
            return kind in (None, "ring", "doorbell")
        return new.state == "on" and (old is None or old.state != "on")

    @callback
    def _on_bell(self, event: Event) -> None:
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if not self._is_ring(old, new):
            return
        now = dt_util.utcnow()
        last = self._last_ring.get(new.entity_id)
        if last is not None and now - last < RING_DEBOUNCE:
            return
        self._last_ring[new.entity_id] = now
        for room, bell in self._bells():
            if bell["entity"] == new.entity_id:
                self.hass.async_create_task(self._async_ring(room, bell))

    def _occupied_rooms(self) -> list[dict[str, Any]]:
        """Rooms where someone probably is (motion lately, or no sensors) and,
        with linked persons, one of them is home."""
        areas = managed_areas(self.hass)
        return [
            room for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            if room.get("area_id") in areas and presence_allows(self.hass, room) and room_occupied(self.hass, room)
        ]

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception:  # noqa: BLE001 - one failing device must not stop the rest
            _LOGGER.exception("Doorbell: %s.%s failed for %s", domain, service, data.get(ATTR_ENTITY_ID))

    async def _async_ring(self, room: dict[str, Any], bell: dict[str, Any]) -> None:
        area = ar.async_get(self.hass).async_get_area(room["area_id"])
        where = area.name if area else room["area_id"]
        local = dt_util.now()
        quiet = in_quiet(bell.get("quiet"), local.hour * 60 + local.minute)
        home = anyone_home(self.hass)
        _LOGGER.debug("Doorbell %s rang (%s, quiet=%s, home=%s)", bell["entity"], where, quiet, home)
        if not quiet and home and not smoke_active(self.hass):
            occupied = self._occupied_rooms()
            players = sorted({p for r in occupied for p in r.get(CONF_MEDIA_PLAYERS, []) or [] if p})
            if bell.get("pause_media", True):
                playing = [p for p in players if (st := self.hass.states.get(p)) is not None and st.state in PLAYING]
                if playing:
                    await self._call("media_player", "media_pause", {ATTR_ENTITY_ID: playing})
            if bell.get("announce"):
                await async_announce(self.hass, text(self.hass, "doorbell_spoken", room=where), occupied_only=True, kind="doorbell")
        nspanel_message(self.hass, "doorbell", text(self.hass, "doorbell_notify", room=where))
        if bell.get("notify", True):
            note = text(self.hass, "doorbell_notify", room=where)
            camera = bell.get("camera")
            cam = self.hass.states.get(camera) if camera else None
            token = cam.attributes.get("access_token") if cam else None
            message = f"{note}\n\n![](/api/camera_proxy/{camera}?token={token})" if token else note
            persistent_notification.async_create(
                self.hass, message, title="RoomControl", notification_id=f"roomcontrol_doorbell_{room['area_id']}"
            )
            self.hass.bus.async_fire("roomcontrol_doorbell", {
                "area_id": room["area_id"], "entity_id": bell["entity"], "camera": camera,
                "quiet": quiet, "nobody_home": not home, "message": note,
            })

    # ── message on the doorbell's screen ───────────────────────────────────

    @callback
    def _on_presence(self, *_: Any) -> None:
        away = bool(household_persons(self.hass)) and not anyone_home(self.hass)
        targets = [
            msg for _room, bell in self._bells()
            if isinstance(msg := bell.get("away_message"), dict) and msg.get("entity") and msg.get("value")
        ]
        if away and not self._away_shown and targets:
            self._away_shown = True
            for msg in targets:
                st = self.hass.states.get(msg["entity"])
                if st is not None and st.state not in ("unavailable", "unknown") and st.state != msg["value"]:
                    self._saved_message[msg["entity"]] = st.state
                self.hass.async_create_task(self._async_set_message(msg["entity"], msg["value"]))
        elif not away and self._away_shown:
            self._away_shown = False
            for entity_id, value in list(self._saved_message.items()):
                self.hass.async_create_task(self._async_set_message(entity_id, value))
            self._saved_message.clear()

    async def _async_set_message(self, entity_id: str, value: str) -> None:
        if entity_id.startswith("select."):
            st = self.hass.states.get(entity_id)
            options = st.attributes.get("options", []) if st else []
            if value not in options:
                _LOGGER.warning("Doorbell: %s has no option %r", entity_id, value)
                return
            await self._call("select", "select_option", {ATTR_ENTITY_ID: entity_id, "option": value})
        elif entity_id.startswith("text."):
            await self._call("text", "set_value", {ATTR_ENTITY_ID: entity_id, "value": value})
