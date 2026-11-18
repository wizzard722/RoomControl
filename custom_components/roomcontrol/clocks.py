"""Alarm clocks per room.

A room can have several alarm clocks (`alarm_clocks` in the room config):

    {"id", "name", "time": "HH:MM", "days": [0..6] (Monday = 0; repeats every
     week), "once": bool, "enabled": bool, "bundles": [bundle ids],
     "snooze": bool, "snoozes": int, "snooze_minutes": int, "persons": [person ids],
     "music": bool, "media_player": entity_id,
     "media": {"media_content_id", "media_content_type"},
     "volume_start": % (first step), "volume_end": % (last step),
     "music_repeat": bool (repeat the music while the clock goes off),
     "stop_music": bool (default yes), "stop_light": bool (default no),
     "covers_open": bool (opens all of the room's curtains),
     "covers_steps": "same" | "own", "covers_snoozes": int,
     "covers_snooze_minutes": int}

When it goes off the chosen bundles go on: without snooze straight at 100%;
with snooze the brightness is spread evenly over the moments it goes off
(3 snoozes: 25% → 50% → 75% → 100%). Each snooze interval it goes one step
brighter by itself; nobody has to press anything (there is no snooze button,
only a stop button). Music (optional) starts on the chosen media player and
gets louder with the steps: volume_start at the first, volume_end at the last.

Stop step: one interval after the last step (without snooze: one interval
after the wake time) it stops by itself when nobody reacted: the music goes off
("stop_music", default yes) and/or the light goes off ("stop_light", default
no). With neither it keeps going until someone stops it.

Curtains (optional) open step by step as well: in the same steps as the light
("same"), or in their own number of steps and interval ("own"). Step i of n
opens them to 100 * (i + 1) / (n + 1) %; curtains without a position open
fully at the first step. Stopping the clock leaves them where they are.

It only goes off when one of its persons (or else the room's persons) is home.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
from homeassistant.util import dt as dt_util

from .smoke import smoke_active
from .const import CONF_COVERS, CONF_GROUPS, CONF_MEDIA_PLAYERS, DOMAIN, SIGNAL_CONFIG_UPDATED
from .control import rc_call
from .rooms import room_persons

_LOGGER = logging.getLogger(__name__)

CONF_ALARM_CLOCKS = "alarm_clocks"
SIGNAL_CLOCKS_UPDATED = f"{DOMAIN}_clocks_updated"


def clock_key(area_id: str, clock_id: str) -> str:
    return f"{area_id}:{clock_id}"


def room_clocks(hass: HomeAssistant) -> list[tuple[str, dict[str, Any]]]:
    """(area_id, clock) for every alarm clock of every room."""
    out: list[tuple[str, dict[str, Any]]] = []
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        for clock in room.get(CONF_ALARM_CLOCKS, []) or []:
            if clock.get("id"):
                out.append((room["area_id"], clock))
    return out


def next_ring(clock: dict[str, Any], now: datetime) -> datetime | None:
    """Next moment the clock goes off (local time), or None if it can't."""
    try:
        hour, minute = (int(x) for x in str(clock.get("time", "")).split(":")[:2])
    except ValueError:
        return None
    days = [d for d in clock.get("days", []) or [] if isinstance(d, int) and 0 <= d <= 6]
    once = bool(clock.get("once")) or not days
    now = dt_util.as_local(now)
    base = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    for add in range(0, 8):
        # Wall-clock arithmetic in the local zone (keeps the time over DST changes).
        candidate = base + timedelta(days=add)
        if not once and candidate.weekday() not in days:
            continue
        if candidate > now:
            return candidate
    return None


class ClockState:
    """What one alarm clock is doing right now."""

    def __init__(self) -> None:
        self.ringing = False  # going off now (light on, music playing)
        self.snoozed_until: datetime | None = None
        self.step = 0
        self.next: datetime | None = None
        self.unsub_next: CALLBACK_TYPE | None = None
        self.unsub_snooze: CALLBACK_TYPE | None = None
        self.unsub_auto_stop: CALLBACK_TYPE | None = None
        self.unsub_covers: CALLBACK_TYPE | None = None
        self.music_on = False
        # The player's repeat mode before the clock set it (restored at stop).
        self.repeat_before: str | None = None

    def cancel(self, *names: str) -> None:
        for name in names or ("unsub_next", "unsub_snooze", "unsub_auto_stop", "unsub_covers"):
            if (unsub := getattr(self, name)) is not None:
                unsub()
                setattr(self, name, None)

    @property
    def active(self) -> bool:
        """Going off or snoozing (waiting to go off again)."""
        return self.ringing or self.snoozed_until is not None


class ClockManager:
    """Schedules and runs all alarm clocks."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.states: dict[str, ClockState] = {}
        self._unsub_signal: CALLBACK_TYPE | None = None

    # ── setup ──────────────────────────────────────────────────────────────

    @callback
    def start(self) -> None:
        self._unsub_signal = async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.sync)
        self.sync()

    @callback
    def stop(self) -> None:
        if self._unsub_signal:
            self._unsub_signal()
            self._unsub_signal = None
        for state in self.states.values():
            state.cancel()
        self.states.clear()

    def find(self, key: str) -> tuple[str, dict[str, Any], dict[str, Any]] | None:
        """(area_id, room, clock) for a clock key."""
        area_id, _, clock_id = key.partition(":")
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") != area_id:
                continue
            for clock in room.get(CONF_ALARM_CLOCKS, []) or []:
                if clock.get("id") == clock_id:
                    return area_id, room, clock
        return None

    @callback
    def sync(self, *_: Any) -> None:
        """(Re)schedule every clock after a config change."""
        keys = set()
        for area_id, clock in room_clocks(self.hass):
            key = clock_key(area_id, clock["id"])
            keys.add(key)
            state = self.states.setdefault(key, ClockState())
            self._schedule_next(key, clock, state)
            if not clock.get("enabled", True) and state.active:
                self._finish(key, state, music_off=True)
        for key in list(self.states.keys() - keys):  # clock removed
            self.states.pop(key).cancel()
        async_dispatcher_send(self.hass, SIGNAL_CLOCKS_UPDATED)

    @callback
    def _schedule_next(self, key: str, clock: dict[str, Any], state: ClockState) -> None:
        state.cancel("unsub_next")
        state.next = next_ring(clock, dt_util.now()) if clock.get("enabled", True) else None
        if state.next is not None:
            @callback
            def _go(_now: Any, k: str = key) -> None:
                self.hass.async_create_task(self._ring(k, 0))

            state.unsub_next = async_track_point_in_time(self.hass, _go, state.next)

    # ── going off ──────────────────────────────────────────────────────────

    def _persons_home(self, room: dict[str, Any], clock: dict[str, Any]) -> bool:
        persons = [p for p in clock.get("persons", []) or [] if p] or room_persons(self.hass, room)
        if not persons:
            return True
        return any((st := self.hass.states.get(p)) is not None and st.state == "home" for p in persons)

    def _lamps(self, room: dict[str, Any], clock: dict[str, Any]) -> list[str]:
        chosen = set(clock.get("bundles", []) or [])
        lamps: list[str] = []
        for group in room.get(CONF_GROUPS, []) or []:
            if group.get("id") in chosen:
                lamps += [e for e in group.get("lights", []) or [] if e not in lamps]
        return lamps

    def lamps_ringing(self, area_id: str) -> set[str]:
        """Lamps of this room's clocks that are going off or snoozing now."""
        out: set[str] = set()
        for key, state in self.states.items():
            if not state.active or not key.startswith(f"{area_id}:"):
                continue
            if (found := self.find(key)) is not None:
                out |= set(self._lamps(found[1], found[2]))
        return out

    @staticmethod
    def snoozes(clock: dict[str, Any]) -> int:
        """How often it can snooze; 0 when snooze is off (then straight to 100%)."""
        if not clock.get("snooze"):
            return 0
        value = clock.get("snoozes", 3)
        return int(min(10, max(0, value))) if isinstance(value, (int, float)) else 3

    @classmethod
    def step_pct(cls, clock: dict[str, Any], step: int) -> int:
        """Brightness at step `step` (0 = first time): 100% spread evenly."""
        n = cls.snoozes(clock)
        return round(100 * (min(step, n) + 1) / (n + 1))

    @classmethod
    def step_volume(cls, clock: dict[str, Any], step: int) -> float:
        """Volume (0-1) at step `step`: from volume_start (first) to volume_end (last)."""
        start = float(clock.get("volume_start", 10)) / 100
        end = float(clock.get("volume_end", 35)) / 100
        n = cls.snoozes(clock)
        level = end if n == 0 else start + (end - start) * min(step, n) / n
        return round(min(1.0, max(0.0, level)), 3)

    @staticmethod
    def stop_actions(clock: dict[str, Any]) -> tuple[bool, bool]:
        """(music off, light off) at the stop step."""
        return bool(clock.get("stop_music", True)), bool(clock.get("stop_light", False))

    @staticmethod
    def _snooze_minutes(clock: dict[str, Any]) -> float:
        minutes = clock.get("snooze_minutes", 5)
        return minutes if isinstance(minutes, (int, float)) and minutes > 0 else 9

    # ── curtains ───────────────────────────────────────────────────────────

    @staticmethod
    def _covers(room: dict[str, Any], clock: dict[str, Any]) -> list[str]:
        """The room's curtains this clock opens: all of them (none when the option is off)."""
        if not clock.get("covers_open"):
            return []
        return [c for c in room.get(CONF_COVERS, []) or [] if c]

    @classmethod
    def cover_steps(cls, clock: dict[str, Any]) -> tuple[int, float]:
        """(number of extra steps, interval in minutes) for the curtains.
        "Step by step" (snooze) off: straight open, like the light."""
        if not clock.get("snooze"):
            return 0, cls._snooze_minutes(clock)
        if clock.get("covers_steps", "same") != "own":
            return cls.snoozes(clock), cls._snooze_minutes(clock)
        n = clock.get("covers_snoozes", 3)
        n = int(min(10, max(0, n))) if isinstance(n, (int, float)) else 3
        minutes = clock.get("covers_snooze_minutes", 5)
        return n, minutes if isinstance(minutes, (int, float)) and minutes > 0 else 9

    @classmethod
    def cover_pct(cls, clock: dict[str, Any], step: int) -> int:
        n, _ = cls.cover_steps(clock)
        return round(100 * (min(step, n) + 1) / (n + 1))

    async def _cover_step(self, key: str, step: int) -> None:
        if smoke_active(self.hass):
            return  # smoke: curtains stay open
        found, state = self.find(key), self.states.get(key)
        if found is None or state is None:
            return
        _, room, clock = found
        covers = self._covers(room, clock)
        if not covers:
            return
        n, minutes = self.cover_steps(clock)
        pct = self.cover_pct(clock, step)
        with_pos = [
            c for c in covers
            if (st := self.hass.states.get(c)) is not None
            and int(st.attributes.get("supported_features", 0)) & 4  # CoverEntityFeature.SET_POSITION
        ]
        without = [c for c in covers if c not in with_pos]
        _LOGGER.debug("Alarm clock %s: curtains to %s%% (step %s)", key, pct, step)
        try:
            if with_pos:
                await rc_call(self.hass, "cover", "set_cover_position", {ATTR_ENTITY_ID: with_pos, "position": pct})
            if without and step == 0:
                await rc_call(self.hass, "cover", "open_cover", {ATTR_ENTITY_ID: without})
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Alarm clock %s: could not move curtains %s", key, covers)
        state.cancel("unsub_covers")
        if step < n:
            @callback
            def _next(_now: Any, k: str = key, s: int = step + 1) -> None:
                self.states[k].unsub_covers = None
                self.hass.async_create_task(self._cover_step(k, s))

            state.unsub_covers = async_call_later(self.hass, minutes * 60, _next)

    async def _ring(self, key: str, step: int) -> None:
        if smoke_active(self.hass):
            return  # smoke: alarm clocks don't switch anything
        found = self.find(key)
        state = self.states.get(key)
        if found is None or state is None:
            return
        area_id, room, clock = found
        light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(area_id)
        if step == 0:
            self._schedule_next(key, clock, state)  # next time, whatever happens now
            if not clock.get("enabled", True):
                return
            if not self._persons_home(room, clock):
                _LOGGER.debug("Alarm clock %s: nobody home, not going off", key)
                if light is not None:
                    light._dbg("blocked", "alarm_clock", self._lamps(room, clock), why="nobody_home",
                               clock=clock.get("name") or clock.get("time"))
                return
            state.cancel("unsub_auto_stop")
            if clock.get("once"):
                await self._disable(area_id, clock["id"])
        state.ringing = True
        state.snoozed_until = None
        state.step = step
        pct = self.step_pct(clock, step)
        _LOGGER.debug("Alarm clock %s goes off (step %s, %s%%)", key, step, pct)
        if (lamps := self._lamps(room, clock)) and light is not None:
            light._dbg("on", "alarm_clock", lamps, pct=pct, clock=clock.get("name") or clock.get("time"))
            await light.async_call_lamps("turn_on", lamps, brightness=round(pct * 255 / 100))
        if step == 0 and self._covers(room, clock):
            await self._cover_step(key, 0)
        if not state.music_on:
            await self._music_start(key, clock, step)
        elif step > 0:
            await self._set_volume(key, clock, step)
        if step >= self.snoozes(clock) and state.unsub_auto_stop is None and any(self.stop_actions(clock)):
            # Last step: the stop step follows one interval later.
            @callback
            def _auto(_now: Any, k: str = key) -> None:
                self.states[k].unsub_auto_stop = None
                self.hass.async_create_task(self.auto_stop(k))

            state.unsub_auto_stop = async_call_later(self.hass, self._snooze_minutes(clock) * 60, _auto)
        # No reaction: after the snooze interval it goes one step brighter anyway
        # (like snoozing, but the music keeps playing), up to 100%.
        state.cancel("unsub_snooze")
        if step < self.snoozes(clock):
            @callback
            def _rise(_now: Any, k: str = key, s: int = step + 1) -> None:
                self.states[k].unsub_snooze = None
                if self.states[k].ringing:
                    self.hass.async_create_task(self._ring(k, s))

            state.unsub_snooze = async_call_later(self.hass, self._snooze_minutes(clock) * 60, _rise)
        async_dispatcher_send(self.hass, SIGNAL_CLOCKS_UPDATED)

    # ── music ──────────────────────────────────────────────────────────────

    def _player(self, key: str, clock: dict[str, Any]) -> str | None:
        """The clock's media player. A room with media players (its Media
        players section) uses those: the clock's own choice if it is one of
        them, else the first. Otherwise the player chosen on the clock."""
        own = clock.get("media_player")
        found = self.find(key)
        room_players = [p for p in (found[1].get(CONF_MEDIA_PLAYERS) or [] if found else []) if p]
        if room_players:
            return own if own in room_players else room_players[0]
        return own

    async def _music_start(self, key: str, clock: dict[str, Any], step: int = 0) -> None:
        player = self._player(key, clock)
        media = clock.get("media") or {}
        # Music is an option (older clocks: on when a player and media were chosen).
        if not clock.get("music", bool(player and media.get("media_content_id"))):
            return
        if not player or not media.get("media_content_id"):
            return
        state = self.states[key]
        try:
            await self.hass.services.async_call(
                "media_player", "volume_set",
                {ATTR_ENTITY_ID: player, "volume_level": self.step_volume(clock, step)}, blocking=True,
            )
            await self.hass.services.async_call(
                "media_player", "play_media",
                {
                    ATTR_ENTITY_ID: player,
                    "media_content_id": media["media_content_id"],
                    "media_content_type": media.get("media_content_type") or "music",
                },
                blocking=True,
            )
        except Exception:  # noqa: BLE001 - a missing or broken player must not stop the light
            _LOGGER.warning("Alarm clock %s: could not start music on %s", key, player, exc_info=True)
            return
        state.music_on = True
        if clock.get("music_repeat"):
            await self._repeat(key, player, "all")

    def _can_repeat(self, player: str) -> bool:
        st = self.hass.states.get(player)
        return st is not None and bool(int(st.attributes.get("supported_features", 0)) & MediaPlayerEntityFeature.REPEAT_SET)

    async def _repeat(self, key: str, player: str, mode: str) -> None:
        """Repeat on (after play_media: some players reset it for new media),
        remembering the player's own mode; or back to that mode."""
        if not self._can_repeat(player):
            _LOGGER.debug("Alarm clock %s: %s can't repeat", key, player)
            return
        state = self.states[key]
        if mode == "all" and state.repeat_before is None:
            st = self.hass.states.get(player)
            state.repeat_before = (st.attributes.get("repeat") if st else None) or "off"
        try:
            await self.hass.services.async_call(
                "media_player", "repeat_set", {ATTR_ENTITY_ID: player, "repeat": mode}, blocking=True
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Alarm clock %s: could not set repeat on %s", key, player)

    async def _set_volume(self, key: str, clock: dict[str, Any], step: int) -> None:
        """Next step: the music gets louder with the light."""
        if not (player := self._player(key, clock)):
            return
        try:
            await self.hass.services.async_call(
                "media_player", "volume_set",
                {ATTR_ENTITY_ID: player, "volume_level": self.step_volume(clock, step)}, blocking=True,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Alarm clock %s: could not set the volume of %s", key, player)

    async def _music_stop(self, key: str, clock: dict[str, Any]) -> None:
        state = self.states[key]
        was_on, state.music_on = state.music_on, False
        if was_on and (player := self._player(key, clock)):
            try:
                await self.hass.services.async_call(
                    "media_player", "media_stop", {ATTR_ENTITY_ID: player}, blocking=True
                )
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Alarm clock %s: could not stop %s", key, player)
        if (before := state.repeat_before) is not None:
            state.repeat_before = None
            if player := self._player(key, clock):
                await self._repeat(key, player, before)

    # ── snooze / stop ──────────────────────────────────────────────────────

    async def snooze(self, key: str) -> None:
        found, state = self.find(key), self.states.get(key)
        if found is None or state is None or not state.ringing:
            return
        _, _, clock = found
        await self._music_stop(key, clock)
        if state.step >= self.snoozes(clock):
            await self.stop(key)  # no snoozes left
            return
        minutes = self._snooze_minutes(clock)
        state.ringing = False
        state.snoozed_until = dt_util.utcnow() + timedelta(minutes=minutes)
        next_step = state.step + 1

        @callback
        def _again(_now: Any, k: str = key, s: int = next_step) -> None:
            self.states[k].unsub_snooze = None
            self.hass.async_create_task(self._ring(k, s))

        state.cancel("unsub_snooze")  # replaces the automatic rise
        state.unsub_snooze = async_call_later(self.hass, minutes * 60, _again)
        async_dispatcher_send(self.hass, SIGNAL_CLOCKS_UPDATED)

    async def stop(self, key: str) -> None:
        """Stop: music off, no more snoozes; the light stays as it is."""
        found, state = self.find(key), self.states.get(key)
        if found is None or state is None:
            return
        if state.active:
            await self._music_stop(key, found[2])
        self._finish(key, state)

    async def auto_stop(self, key: str) -> None:
        """Stop step (no reaction): music and/or light off, as chosen."""
        found, state = self.find(key), self.states.get(key)
        if found is None or state is None or not state.active:
            return
        area_id, room, clock = found
        music_off, light_off = self.stop_actions(clock)
        if music_off:
            await self._music_stop(key, clock)
        if light_off:
            light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(area_id)
            if (lamps := self._lamps(room, clock)) and light is not None:
                light._dbg("off", "alarm_clock_stop", lamps, clock=clock.get("name") or clock.get("time"))
                await light.async_call_lamps("turn_off", lamps)
        if music_off or not state.music_on:
            self._finish(key, state)
        else:
            # Light off, music keeps playing: the clock goes on until it is stopped.
            state.cancel("unsub_snooze", "unsub_covers")
            async_dispatcher_send(self.hass, SIGNAL_CLOCKS_UPDATED)

    @callback
    def _finish(self, key: str, state: ClockState, music_off: bool = False) -> None:
        if music_off and (found := self.find(key)) is not None:
            self.hass.async_create_task(self._music_stop(key, found[2]))
        state.ringing = False
        state.snoozed_until = None
        state.step = 0
        state.cancel("unsub_snooze", "unsub_auto_stop", "unsub_covers")
        async_dispatcher_send(self.hass, SIGNAL_CLOCKS_UPDATED)

    async def set_enabled(self, key: str, enabled: bool) -> None:
        found = self.find(key)
        if found is None:
            return
        area_id, _, clock = found
        await self._save_clock(area_id, clock["id"], {"enabled": enabled})

    async def _disable(self, area_id: str, clock_id: str) -> None:
        await self._save_clock(area_id, clock_id, {"enabled": False})

    async def _save_clock(self, area_id: str, clock_id: str, patch: dict[str, Any]) -> None:
        from . import _async_save  # here: avoids an import cycle

        rooms = []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == area_id:
                room = {
                    **room,
                    CONF_ALARM_CLOCKS: [
                        {**c, **patch} if c.get("id") == clock_id else c
                        for c in room.get(CONF_ALARM_CLOCKS, []) or []
                    ],
                }
            rooms.append(room)
        await _async_save(self.hass, rooms=rooms)
