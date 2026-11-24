"""Locks per room: they go on lock by themselves, never open.

Per lock (room option `locks`, see const.CONF_LOCKS):
- lock times ("Wanneer op slot"): [{"name", "days": [0..6] (Monday = 0),
  "time": "HH:MM", "holiday": "normal" | "vacation_home" (verlof) |
  "vacation_away" (vakantie)}]. At that time on those
  days the lock is locked (if it is open). During vacation the vacation times
  count — or, when there are none, the normal ones. A time with
  "enabled": false is off (kept, but it does nothing). The older lock-wide
  "slots_enabled": false still switches all times off. (Older settings
  stored time slots with a "start"; their start time counts.)
- "away_lock": nobody home (all persons in the general settings away) for
  "away_minutes" → locked; also when it is opened while nobody is home.

Checked every minute and right after a config change. A lock that does not
lock (jammed, unavailable) is tried again at most every RETRY minutes.

Missed times: RoomControl remembers when it last checked (.storage/
roomcontrol.locks). A lock time that passed while Home Assistant was not
running (a restart, an update) is done right after startup, once the lock is
available again (at most CATCH_UP_WAIT after startup; times longer ago than
CATCH_UP_MAX are not caught up).
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .smoke import smoke_active
from .const import (
    DOMAIN,
    LOCK_AWAY_MINUTES_DEFAULT,
    SIGNAL_CONFIG_UPDATED,
)
from .rooms import anyone_home, managed_areas, room_locks
from .slots import hm_minutes, mode_slots

_LOGGER = logging.getLogger(__name__)

UNLOCKED_STATES = ("unlocked", "open")
RETRY = timedelta(minutes=5)
# A lock time still counts this long after it passed (a missed check).
LATE = 5  # minutes
STORAGE_KEY = "roomcontrol.locks"
SAVE_DELAY = 10  # s
# Times missed while Home Assistant was down: at most this far back...
CATCH_UP_MAX = timedelta(days=2)
# ...and the lock gets this long after startup to become available.
CATCH_UP_WAIT = timedelta(minutes=30)


def lock_key(area_id: str, entity_id: str) -> str:
    return f"{area_id}:{entity_id}"


def _minutes(value: Any, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) and value >= 0 else default


class LockManager:
    """Locks the rooms' locks by their slots and when nobody is home."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._done: dict[str, str] = {}  # per lock time: the date it last locked
        self._tried: dict[str, datetime] = {}  # last lock attempt, per lock
        self._away_since: datetime | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        # When RoomControl last checked the locks (before this start: from storage).
        self._last_seen: datetime | None = None
        self._started = dt_util.utcnow()
        # Locks with a time missed while Home Assistant was down: key → that time.
        self._catch_up: dict[str, datetime] = {}
        self._catch_up_done = False

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            self._last_seen = dt_util.parse_datetime(stored.get("last_seen") or "")

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.evaluate))
        self.evaluate()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @callback
    def _tick(self, _now: Any) -> None:
        self.evaluate()

    def _log(self, area_id: str, reason: str, entity_id: str, **detail: Any) -> None:
        """Into the room's debug log (panel)."""
        entity = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(area_id)
        if entity is None:
            return
        st = self.hass.states.get(entity_id)
        name = (st.attributes.get("friendly_name") if st else None) or entity_id
        entity._dbg("lock", reason, device=name, **detail)

    def next_time(self, lock: dict[str, Any], now: datetime) -> datetime | None:
        """When the lock goes on lock next by its times (None: no times on)."""
        if lock.get("slots_enabled") is False:
            return None
        vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
        local = dt_util.as_local(now)
        for offset in range(8):
            day = local + timedelta(days=offset)
            best: datetime | None = None
            for entry in mode_slots(lock.get("slots", []), vacation):
                if entry.get("enabled") is False:
                    continue
                at = self._time_of(entry)
                days = {d for d in entry.get("days", []) or [] if isinstance(d, int)}
                if at is None or day.weekday() not in days:
                    continue
                when = day.replace(hour=at // 60, minute=at % 60, second=0, microsecond=0)
                if when > local and (best is None or when < best):
                    best = when
            if best is not None:
                return best
        return None

    def lock_info(self, area_id: str, lock: dict[str, Any], now: datetime) -> dict[str, Any]:
        """What the lock does now (panel debug)."""
        key = lock_key(area_id, lock["entity_id"])
        nxt = self.next_time(lock, now)
        return {
            "next": nxt.isoformat() if nxt else None,
            "away_lock": bool(lock.get("away_lock")),
            "away_minutes": _minutes(lock.get("away_minutes"), LOCK_AWAY_MINUTES_DEFAULT),
            "nobody_home_since": self._away_since.isoformat() if self._away_since else None,
            "catch_up": self._catch_up[key].isoformat() if key in self._catch_up else None,
        }

    @callback
    def _remember_seen(self, now: datetime) -> None:
        self._store.async_delay_save(lambda: {"last_seen": now.isoformat()}, SAVE_DELAY)

    def missed_time(self, lock: dict[str, Any], since: datetime, now: datetime) -> datetime | None:
        """The latest lock time of `lock` after `since` and before now (local
        days, vacation mode as it is now); None: none was missed."""
        if lock.get("slots_enabled") is False:
            return None
        since = max(since, now - CATCH_UP_MAX)
        vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
        local_now, local_since = dt_util.as_local(now), dt_util.as_local(since)
        latest: datetime | None = None
        day = local_since.date()
        while day <= local_now.date():
            for entry in mode_slots(lock.get("slots", []), vacation):
                if entry.get("enabled") is False:
                    continue
                at = self._time_of(entry)
                days = {d for d in entry.get("days", []) or [] if isinstance(d, int)}
                if at is None or day.weekday() not in days:
                    continue
                when = local_now.replace(
                    year=day.year, month=day.month, day=day.day,
                    hour=at // 60, minute=at % 60, second=0, microsecond=0,
                )
                if local_since < when <= local_now and (latest is None or when > latest):
                    latest = when
            day += timedelta(days=1)
        return latest

    @callback
    def _find_missed(self, now: datetime) -> None:
        """Once, at startup: which locks had a time while Home Assistant was down."""
        self._catch_up_done = True
        if self._last_seen is None:
            return  # first start: nothing to catch up
        areas = managed_areas(self.hass)
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") not in areas:
                continue
            for lock in room_locks(room):
                if (when := self.missed_time(lock, self._last_seen, now)) is not None:
                    key = lock_key(room["area_id"], lock["entity_id"])
                    self._catch_up[key] = when
                    self._log(room["area_id"], "lock_missed_found", lock["entity_id"], time=dt_util.as_local(when).strftime("%H:%M"))
                    _LOGGER.info("Lock %s: time %s was missed (restart), locking it now", lock["entity_id"], when)

    # ── helpers ────────────────────────────────────────────────────────────

    def _settings(self) -> dict[str, Any]:
        return self.hass.data.get(DOMAIN, {}).get("settings", {})

    @staticmethod
    def _time_of(entry: dict[str, Any]) -> int | None:
        """Minutes after midnight of a lock time (older settings: a slot's start time)."""
        if "time" in entry:
            return hm_minutes(entry.get("time"))
        start = entry.get("start") or {}
        return hm_minutes(start.get("time")) if start.get("type", "time") == "time" else None

    def due_times(self, key: str, lock: dict[str, Any], now: datetime) -> list[int]:
        """The lock's times (minutes after midnight) that are due now and did not lock today yet."""
        if lock.get("slots_enabled") is False:
            return []
        now = dt_util.as_local(now)
        t = now.hour * 60 + now.minute
        vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
        entries = mode_slots(lock.get("slots", []), vacation)
        today = now.date().isoformat()
        due = []
        for entry in entries:
            if entry.get("enabled") is False:
                continue
            at = self._time_of(entry)
            days = {d for d in entry.get("days", []) or [] if isinstance(d, int)}
            if at is None or now.weekday() not in days or not 0 <= t - at < LATE:
                continue
            if self._done.get(f"{key}#{at}") != today and at not in due:
                due.append(at)
        return due

    def find(self, area_id: str, entity_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") != area_id:
                continue
            for lock in room_locks(room):
                if lock["entity_id"] == entity_id:
                    return room, lock
        return None

    # ── checking ───────────────────────────────────────────────────────────

    @callback
    def evaluate(self, *_: Any) -> None:
        if smoke_active(self.hass):
            return  # smoke: no lock goes on lock by itself
        now = dt_util.utcnow()
        if not self._catch_up_done:
            self._find_missed(now)
        self._remember_seen(now)
        if anyone_home(self.hass):
            self._away_since = None
        elif self._away_since is None:
            self._away_since = now
        areas = managed_areas(self.hass)
        seen: set[str] = set()
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            area_id = room.get("area_id")
            if area_id not in areas:
                continue
            for lock in room_locks(room):
                key = lock_key(area_id, lock["entity_id"])
                seen.add(key)
                self._check(key, room, lock, now)
        for key in list(self._tried.keys() - seen):
            self._tried.pop(key, None)
        for key in list(self._catch_up.keys() - seen):
            self._catch_up.pop(key, None)

    @callback
    def _check(self, key: str, room: dict[str, Any], lock: dict[str, Any], now: datetime) -> None:
        entity_id = lock["entity_id"]
        due = self.due_times(key, lock, now)
        today = dt_util.as_local(now).date().isoformat()
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unavailable", "unknown"):
            # Not (yet) available, e.g. just after a restart: a due time stays
            # due (within LATE) and a missed one waits (up to CATCH_UP_WAIT).
            if key in self._catch_up and now - self._started > CATCH_UP_WAIT:
                _LOGGER.warning("Lock %s: still unavailable, the missed time is not caught up", entity_id)
                self._log(room["area_id"], "lock_missed_gave_up", entity_id)
                self._catch_up.pop(key, None)
            elif due:
                self._log(room["area_id"], "lock_unavailable", entity_id)
            return
        for at in due:
            self._done[f"{key}#{at}"] = today  # once per day, open or not
        missed = self._catch_up.pop(key, None)
        if state.state not in UNLOCKED_STATES:
            if due or missed is not None:
                self._log(room["area_id"], "lock_already_locked", entity_id)
            self._tried.pop(key, None)
            return
        reason = None
        if due:
            reason = "time"
        elif missed is not None:
            reason = "missed time"
        elif lock.get("away_lock") and self._away_since is not None:
            wait = timedelta(minutes=_minutes(lock.get("away_minutes"), LOCK_AWAY_MINUTES_DEFAULT))
            if now - self._away_since >= wait and now - state.last_changed >= min(wait, timedelta(minutes=1)):
                reason = "away"
        if reason is None:
            return
        if reason == "away" and (last := self._tried.get(key)) is not None and now - last < RETRY:
            return
        self._tried[key] = now
        _LOGGER.debug("Lock %s: locking (%s)", entity_id, reason)
        self._log(room["area_id"], {"time": "lock_time", "missed time": "lock_missed", "away": "lock_away"}[reason], entity_id)
        self.hass.async_create_task(self._lock([entity_id], room["area_id"]))

    async def _lock(self, entity_ids: list[str], area_id: str | None = None) -> None:
        try:
            await self.hass.services.async_call("lock", "lock", {ATTR_ENTITY_ID: entity_ids}, blocking=True)
        except Exception:  # noqa: BLE001 - a jammed or missing lock must not stop the rest
            _LOGGER.warning("Could not lock %s", entity_ids, exc_info=True)
            if area_id:
                for entity_id in entity_ids:
                    self._log(area_id, "lock_failed", entity_id)

    async def lock_room(self, area_id: str) -> None:
        """"Alles op slot": every lock of the room."""
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == area_id and (ids := [l["entity_id"] for l in room_locks(room)]):
                await self._lock(ids)

    async def set_option(self, area_id: str, entity_id: str, patch: dict[str, Any]) -> None:
        """Change one lock's settings (from its switches on the room's device)."""
        from . import _async_save  # here: avoids an import cycle

        rooms = []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == area_id:
                room = {
                    **room,
                    "locks": [
                        {**l, **patch} if isinstance(l, dict) and l.get("entity_id") == entity_id else l
                        for l in room.get("locks", []) or []
                    ],
                }
            rooms.append(room)
        await _async_save(self.hass, rooms=rooms)
