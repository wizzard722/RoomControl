"""Full control: a room's lamps and curtains only follow RoomControl.

Every light/cover command RoomControl gives (its automations, its own entities
in Home Assistant and the panel) goes through `rc_call`, which remembers what
each lamp or curtain should be. For rooms with full control switched on, any
other change (a wall switch, another app, an automation, the device itself) is
put back to that remembered state. A lamp or curtain RoomControl has not
commanded yet keeps the state it had.

Right after a RoomControl command there is a short grace period (lamps fade,
curtains move), in which differences are not corrected yet; once it is over
the state is checked again. While the room is in manual control nothing is put
back, and what is changed then becomes the new state to keep.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COVERS,
    CONF_FULL_CONTROL,
    DOMAIN,
    FULL_CONTROL_COVER_GRACE,
    FULL_CONTROL_LAMP_GRACE,
    FULL_CONTROL_MAX_REVERTS,
    SIGNAL_CONFIG_UPDATED,
)
from .covers_known import CLOSED, known_cover
from .rooms import cover_state, inverted_covers, managed_areas, swap_cover

_LOGGER = logging.getLogger(__name__)

BRIGHTNESS_TOLERANCE = 5  # of 255
POSITION_TOLERANCE = 5  # percent


def _wanted(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("wanted", {})


def _ids(data: dict[str, Any]) -> list[str]:
    ids = data.get(ATTR_ENTITY_ID) or []
    return [ids] if isinstance(ids, str) else list(ids)


@callback
def record(hass: HomeAssistant, domain: str, service: str, data: dict[str, Any]) -> None:
    """Remember what RoomControl asked of each lamp / curtain."""
    wanted = _wanted(hass)
    now = dt_util.utcnow()
    for entity_id in _ids(data):
        previous = wanted.get(entity_id) or {}
        if domain == "light" and service == "turn_on":
            brightness = data.get("brightness")
            if brightness is None and isinstance(data.get("brightness_pct"), (int, float)):
                brightness = round(data["brightness_pct"] * 255 / 100)
            if brightness is None and previous.get("on"):
                brightness = previous.get("brightness")  # e.g. only the colour changed
            wanted[entity_id] = {"on": True, "brightness": brightness, "at": now}
        elif domain == "light" and service == "turn_off":
            wanted[entity_id] = {"on": False, "at": now}
        elif domain == "cover" and service == "open_cover":
            wanted[entity_id] = {"cover": "open", "at": now}
        elif domain == "cover" and service == "close_cover":
            wanted[entity_id] = {"cover": "closed", "at": now}
        elif domain == "cover" and service == "set_cover_position" and "position" in data:
            wanted[entity_id] = {"position": int(data["position"]), "at": now}
        else:
            # toggle, stop, …: the result is accepted once it has settled
            wanted[entity_id] = {"free": True, "at": now}


async def rc_call(
    hass: HomeAssistant, domain: str, service: str, data: dict[str, Any], blocking: bool = True,
    invert: bool = True,
) -> None:
    """A light/cover service call by RoomControl (remembered for full control).

    Curtains marked as reversed get the opposite open/close command; a
    position is sent as it is (the curtain's position is the right way
    round). What is remembered is what RoomControl wanted (open, closed or a
    position), so full control compares it with the curtain's real state
    (invert=False: send the commands exactly as given)."""
    record(hass, domain, service, data)
    if domain == "cover" and invert and service in ("open_cover", "close_cover"):
        reversed_ = inverted_covers(hass)
        ids = _ids(data)
        flip = [e for e in ids if e in reversed_]
        if flip:
            keep = [e for e in ids if e not in reversed_]
            rest = {k: v for k, v in data.items() if k != ATTR_ENTITY_ID}
            if keep:
                await hass.services.async_call(domain, service, {**rest, ATTR_ENTITY_ID: keep}, blocking=blocking)
            await hass.services.async_call(domain, swap_cover(service), {**rest, ATTR_ENTITY_ID: flip}, blocking=blocking)
            return
    await hass.services.async_call(domain, service, data, blocking=blocking)


def _from_state(hass: HomeAssistant, state: State) -> dict[str, Any]:
    """What to keep when RoomControl has not commanded the entity yet."""
    if state.domain == "light":
        return {"on": state.state == "on", "brightness": state.attributes.get("brightness"), "at": None}
    known = known_cover(hass, state.entity_id)
    if known and known["source"] == "roomcontrol":
        if isinstance(known["position"], (int, float)):
            return {"position": int(known["position"]), "at": None}
        return {"cover": "closed" if known["state"] == CLOSED else "open", "at": None}
    position = state.attributes.get("current_position")
    if isinstance(position, (int, float)):
        return {"position": int(position), "at": None}
    return {"cover": "open" if cover_state(hass, state) in ("open", "opening") else "closed", "at": None}


def _matches(hass: HomeAssistant, state: State, wanted: dict[str, Any]) -> bool:
    if state.domain == "light":
        if (state.state == "on") != bool(wanted.get("on")):
            return False
        want, have = wanted.get("brightness"), state.attributes.get("brightness")
        if wanted.get("on") and isinstance(want, (int, float)) and isinstance(have, (int, float)):
            return abs(want - have) <= BRIGHTNESS_TOLERANCE
        return True
    # Curtains: the state RoomControl knows (every open/close/position command
    # in Home Assistant), not the curtain's own state, which is often wrong.
    known = known_cover(hass, state.entity_id)
    if known and known["source"] == "roomcontrol":
        if "position" in wanted:
            return known["position"] is None or abs(known["position"] - wanted["position"]) <= POSITION_TOLERANCE
        if wanted.get("cover") == "open":
            return known["state"] != CLOSED
        if wanted.get("cover") == "closed":
            return known["state"] == CLOSED
        return True
    if "position" in wanted:
        have = state.attributes.get("current_position")
        if isinstance(have, (int, float)):
            return abs(have - wanted["position"]) <= POSITION_TOLERANCE and state.state not in ("opening", "closing")
        return True
    if wanted.get("cover") == "open":
        return cover_state(hass, state) in ("open", "opening")
    if wanted.get("cover") == "closed":
        return cover_state(hass, state) in ("closed", "closing")
    return True


def _restore_call(entity_id: str, wanted: dict[str, Any]) -> tuple[str, str, dict[str, Any]] | None:
    domain = entity_id.split(".", 1)[0]
    if domain == "light":
        if not wanted.get("on"):
            return "light", "turn_off", {ATTR_ENTITY_ID: entity_id}
        data: dict[str, Any] = {ATTR_ENTITY_ID: entity_id}
        if isinstance(wanted.get("brightness"), (int, float)):
            data["brightness"] = int(wanted["brightness"])
        return "light", "turn_on", data
    if "position" in wanted:
        return "cover", "set_cover_position", {ATTR_ENTITY_ID: entity_id, "position": wanted["position"]}
    if wanted.get("cover") == "open":
        return "cover", "open_cover", {ATTR_ENTITY_ID: entity_id}
    if wanted.get("cover") == "closed":
        return "cover", "close_cover", {ATTR_ENTITY_ID: entity_id}
    return None


class FullControl:
    """Puts lamps and curtains of full-control rooms back to what RoomControl wants."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._room_of: dict[str, str] = {}
        self._unsub_states: CALLBACK_TYPE | None = None
        self._unsub_signal: CALLBACK_TYPE | None = None
        self._rechecks: dict[str, CALLBACK_TYPE] = {}
        self._reverts: dict[str, list[datetime]] = {}

    @callback
    def start(self) -> None:
        mem = self.hass.data.get(DOMAIN, {}).get("memory")
        if mem is not None:
            # What each lamp/curtain should be, from before the restart: a change
            # made while Home Assistant was down is put back too.
            stored = mem.get("full_control")
            if isinstance(stored, dict):
                wanted = _wanted(self.hass)
                for entity_id, want in stored.items():
                    if isinstance(want, dict) and entity_id not in wanted:
                        at = dt_util.parse_datetime(want.get("at") or "") if isinstance(want.get("at"), str) else None
                        wanted[entity_id] = {**want, "at": at}
            self._unsub_memory = mem.register("full_control", self._memory_data)
        self._unsub_signal = async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync)
        self._sync()

    def _memory_data(self) -> dict[str, Any] | None:
        wanted = {
            e: {**w, "at": w["at"].isoformat() if isinstance(w.get("at"), datetime) else None}
            for e, w in _wanted(self.hass).items() if e in self._room_of
        }
        return wanted or None

    @callback
    def stop(self) -> None:
        if getattr(self, "_unsub_memory", None):
            self._unsub_memory()
            self._unsub_memory = None
        if self._unsub_signal:
            self._unsub_signal()
            self._unsub_signal = None
        if self._unsub_states:
            self._unsub_states()
            self._unsub_states = None
        for cancel in self._rechecks.values():
            cancel()
        self._rechecks.clear()

    @callback
    def _sync(self, *_: Any) -> None:
        """Track the lamps and curtains of every room with full control."""
        areas = managed_areas(self.hass)
        room_of: dict[str, str] = {}
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            area_id = room.get("area_id")
            if area_id not in areas or not room.get(CONF_FULL_CONTROL):
                continue
            for light in room.get("lights", []) or []:
                if (eid := light.get("entity_id") if isinstance(light, dict) else light):
                    room_of[eid] = area_id
            for cover in room.get(CONF_COVERS, []) or []:
                if cover:
                    room_of[cover] = area_id
        if room_of == self._room_of:
            return
        # Entities that leave full control start fresh if they come back.
        for eid in self._room_of.keys() - room_of.keys():
            _wanted(self.hass).pop(eid, None)
            if cancel := self._rechecks.pop(eid, None):
                cancel()
        self._room_of = room_of
        if self._unsub_states:
            self._unsub_states()
            self._unsub_states = None
        if room_of:
            self._unsub_states = async_track_state_change_event(self.hass, list(room_of), self._on_change)

    def _manual(self, entity_id: str) -> bool:
        entity = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(self._room_of.get(entity_id))
        return bool(entity is not None and getattr(entity, "_manual", False))

    @staticmethod
    def _grace(entity_id: str) -> float:
        return FULL_CONTROL_LAMP_GRACE if entity_id.startswith("light.") else FULL_CONTROL_COVER_GRACE

    @callback
    def _on_change(self, event: Event) -> None:
        entity_id: str = event.data["entity_id"]
        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        if new is None or new.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        wanted = _wanted(self.hass)
        if self._manual(entity_id):
            wanted.pop(entity_id, None)  # manual control: what is set now is kept afterwards
            return
        now = dt_util.utcnow()
        want = wanted.get(entity_id)
        if want is not None and want.get("free"):
            if want["at"] and now - want["at"] < timedelta(seconds=self._grace(entity_id)):
                return
            want = None
        if want is None:
            if old is None or old.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                wanted[entity_id] = _from_state(self.hass, new)  # first known state: keep that
                return
            want = wanted[entity_id] = _from_state(self.hass, old)
        self._check(entity_id, new, want, now)

    @callback
    def _check(self, entity_id: str, state: State, want: dict[str, Any], now: datetime) -> None:
        if _matches(self.hass, state, want):
            return
        if want.get("at"):
            left = self._grace(entity_id) - (now - want["at"]).total_seconds()
            if left > 0:  # still fading / moving after RoomControl's command
                if entity_id not in self._rechecks:
                    self._rechecks[entity_id] = async_call_later(
                        self.hass, left + 0.5, self._recheck_cb(entity_id)
                    )
                return
        self._restore(entity_id, want, now)

    def _recheck_cb(self, entity_id: str) -> Callable[[Any], None]:
        @callback
        def _recheck(_now: Any) -> None:
            self._rechecks.pop(entity_id, None)
            state = self.hass.states.get(entity_id)
            want = _wanted(self.hass).get(entity_id)
            if (
                state is None or want is None or want.get("free")
                or entity_id not in self._room_of or self._manual(entity_id)
            ):
                return
            self._check(entity_id, state, want, dt_util.utcnow())

        return _recheck

    @callback
    def _restore(self, entity_id: str, want: dict[str, Any], now: datetime) -> None:
        recent = [t for t in self._reverts.get(entity_id, []) if now - t < timedelta(minutes=1)]
        if len(recent) >= FULL_CONTROL_MAX_REVERTS:
            _LOGGER.warning(
                "Full control: %s keeps changing; not putting it back again for now", entity_id
            )
            self._reverts[entity_id] = recent
            return
        call = _restore_call(entity_id, want)
        if call is None:
            return
        self._reverts[entity_id] = [*recent, now]
        _LOGGER.debug("Full control: %s changed from outside, back to %s", entity_id, want)
        # `want` is what was meant (open/closed): reversed curtains get it swapped again.
        self.hass.async_create_task(rc_call(self.hass, *call))
