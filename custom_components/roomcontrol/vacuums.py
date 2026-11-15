"""Vacuum cleaners per room: cleaning moments, presence and the alarm.

A room can have vacuum cleaners (`vacuums`, vacuum.* ids; the first one is
used) and cleaning moments (`vacuum_plans`):

    {"id", "name", "enabled": bool,
     "time": "HH:MM", "days": [0..6] (Monday = 0),
     "home_persons": [person ids], "alarm_states": ["disarmed" | "armed_home" |
                                "armed_away"]: it may start when one of these
                                persons is home OR the alarm is in one of these
                                states (nothing chosen: always),
     "retry": bool, "retry_until": "HH:MM"}  someone home at the moment: start
                                as soon as everybody has left, until that time.

Vacuum persons: the general setting `vacuum_persons` (missing = all persons
RoomControl follows).

The alarm (the general settings' alarm panel): when a moment starts the
vacuum while nobody is home, the alarm goes to Armed Home first (so the
vacuum doesn't set it off). When that run is over (the vacuum is docked or
idle again): somebody home → nothing; nobody home → Armed Away.

When a run RoomControl started is over, the room counts as vacuumed at that
moment (`last_clean`, kept across restarts; the panel shows it until the
next day begins).
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_track_point_in_time, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .smoke import smoke_active
from .clocks import next_ring
from .const import DOMAIN, SETTING_ALARM_ENTITY, SETTING_PERSONS, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

CONF_VACUUMS = "vacuums"
CONF_VACUUM_PLANS = "vacuum_plans"
# Room option: cleaning moments on (default) or off — the "Stofzuiger" switch
# on the room's device in Home Assistant, and the switch in the panel.
CONF_VACUUM_ENABLED = "vacuum_enabled"
SETTING_VACUUM_PERSONS = "vacuum_persons"
SIGNAL_VACUUM_UPDATED = f"{DOMAIN}_vacuum_updated"

# Vacuum states: busy vs. done.
BUSY = {"cleaning", "returning"}
DONE = {"docked", "idle"}


def plan_key(area_id: str, plan_id: str) -> str:
    return f"{area_id}:{plan_id}"


def _hhmm(value: Any) -> tuple[int, int] | None:
    try:
        hour, minute = (int(x) for x in str(value).split(":")[:2])
    except ValueError:
        return None
    return (hour, minute) if 0 <= hour < 24 and 0 <= minute < 60 else None


class PlanState:
    """What one cleaning moment is doing right now."""

    def __init__(self) -> None:
        self.next: datetime | None = None
        self.unsub_next: CALLBACK_TYPE | None = None
        self.waiting_until: datetime | None = None  # retry: start when everybody left
        self.last_run: datetime | None = None
        self.last_note: str | None = None  # why it didn't start (for the panel)

    def cancel(self) -> None:
        if self.unsub_next is not None:
            self.unsub_next()
            self.unsub_next = None


class VacuumManager:
    """Runs the cleaning moments of all rooms."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.states: dict[str, PlanState] = {}
        # vacuum entity -> True when RoomControl started the run and nobody was home
        self.runs: dict[str, dict[str, Any]] = {}
        self._unsubs: list[CALLBACK_TYPE] = []
        self._unsub_tracked: CALLBACK_TYPE | None = None
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}_vacuum")
        self.last_clean: dict[str, str] = {}  # area_id -> ISO time the last run ended

    # ── setup ──────────────────────────────────────────────────────────────

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        self.last_clean = dict(stored.get("last_clean") or {})
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.sync))
        self.sync()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._unsub_tracked:
            self._unsub_tracked()
            self._unsub_tracked = None
        for state in self.states.values():
            state.cancel()
        self.states.clear()

    def _rooms(self) -> list[dict[str, Any]]:
        return self.hass.data.get(DOMAIN, {}).get("rooms", [])

    def plans(self) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
        """(area_id, room, plan) for every cleaning moment of a room with a vacuum."""
        out = []
        for room in self._rooms():
            if not self.vacuum(room):
                continue
            for plan in room.get(CONF_VACUUM_PLANS, []) or []:
                if plan.get("id"):
                    out.append((room["area_id"], room, plan))
        return out

    def find(self, key: str) -> tuple[str, dict[str, Any], dict[str, Any]] | None:
        for area_id, room, plan in self.plans():
            if plan_key(area_id, plan["id"]) == key:
                return area_id, room, plan
        return None

    @staticmethod
    def vacuum(room: dict[str, Any]) -> str | None:
        return next((v for v in room.get(CONF_VACUUMS, []) or [] if v), None)

    @callback
    def sync(self, *_: Any) -> None:
        """(Re)schedule every moment and (re)track vacuums, schedules and persons."""
        keys = set()
        settings = self.hass.data.get(DOMAIN, {}).get("settings", {})
        tracked: set[str] = {p for p in settings.get(SETTING_PERSONS, []) or [] if p}
        if alarm := settings.get(SETTING_ALARM_ENTITY):
            tracked.add(alarm)
        for area_id, room, plan in self.plans():
            key = plan_key(area_id, plan["id"])
            keys.add(key)
            state = self.states.setdefault(key, PlanState())
            self._schedule_next(key, plan, state)
            if vac := self.vacuum(room):
                tracked.add(vac)
        for key in list(self.states.keys() - keys):
            self.states.pop(key).cancel()
        tracked |= set(self.runs)
        if self._unsub_tracked:
            self._unsub_tracked()
        self._unsub_tracked = (
            async_track_state_change_event(self.hass, sorted(tracked), self._on_change) if tracked else None
        )
        async_dispatcher_send(self.hass, SIGNAL_VACUUM_UPDATED)

    @callback
    def _schedule_next(self, key: str, plan: dict[str, Any], state: PlanState) -> None:
        state.cancel()
        state.next = None
        if not plan.get("enabled", True):
            return
        if not plan.get("days"):
            return
        state.next = next_ring({"time": plan.get("time"), "days": plan.get("days")}, dt_util.now())
        if state.next is not None:
            @callback
            def _go(_now: Any, k: str = key) -> None:
                self.hass.async_create_task(self._moment(k))

            state.unsub_next = async_track_point_in_time(self.hass, _go, state.next)

    # ── persons ────────────────────────────────────────────────────────────

    def persons(self) -> list[str]:
        settings = self.hass.data.get(DOMAIN, {}).get("settings", {})
        followed = [p for p in settings.get(SETTING_PERSONS, []) or [] if p]
        chosen = settings.get(SETTING_VACUUM_PERSONS)
        return followed if chosen is None else [p for p in followed if p in chosen]

    def anyone_home(self) -> bool:
        return any((st := self.hass.states.get(p)) is not None and st.state == "home" for p in self.persons())

    # ── going ──────────────────────────────────────────────────────────────

    async def _moment(self, key: str) -> None:
        """A moment's time has come (or its schedule turned on)."""
        found, state = self.find(key), self.states.get(key)
        if found is None or state is None:
            return
        _, room, plan = found
        self._schedule_next(key, plan, state)  # next time, whatever happens now
        if not plan.get("enabled", True):
            return
        if not room.get(CONF_VACUUM_ENABLED, True):
            state.last_note = "switched_off"
            _LOGGER.debug("Vacuum %s: switched off for this room, not starting", key)
            return
        if (why := self.blocked(plan)) is not None:
            until = self._retry_until(plan)
            if until is not None:
                state.waiting_until = until
                state.last_note = "waiting"
                _LOGGER.debug("Vacuum %s: %s, waiting until %s", key, why, until)
            else:
                state.last_note = why
                _LOGGER.debug("Vacuum %s: %s, not starting", key, why)
            async_dispatcher_send(self.hass, SIGNAL_VACUUM_UPDATED)
            return
        await self.start_clean(key)

    @staticmethod
    def home_persons(plan: dict[str, Any]) -> list[str]:
        """Persons of whom at least one must be home for this moment."""
        return [p for p in plan.get("home_persons", []) or [] if p]

    def _alarm_state(self) -> str | None:
        alarm = self.hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ALARM_ENTITY)
        st = self.hass.states.get(alarm) if alarm else None
        return st.state if st is not None else None

    def blocked(self, plan: dict[str, Any]) -> str | None:
        """Why the moment may not start now ("not_allowed"), or None.

        It may start when one of its persons is home OR the alarm is in one
        of its states. Nothing chosen: always."""
        persons = self.home_persons(plan)
        states = [s for s in plan.get("alarm_states", []) or [] if s]
        if not persons and not states:
            return None
        if any((st := self.hass.states.get(p)) is not None and st.state == "home" for p in persons):
            return None
        if states and self._alarm_state() in states:
            return None
        return "not_allowed"

    def _retry_until(self, plan: dict[str, Any]) -> datetime | None:
        if not plan.get("retry"):
            return None
        hm = _hhmm(plan.get("retry_until") or "18:00")
        if hm is None:
            return None
        now = dt_util.now()
        until = now.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
        return until if until > now else None

    async def start_clean(self, key: str | None = None, area_id: str | None = None) -> bool:
        """Start the room's vacuum (a moment, or "clean now" from the panel)."""
        if smoke_active(self.hass):
            return False  # smoke: the vacuum stays docked
        if key is not None:
            found = self.find(key)
            if found is None:
                return False
            area_id, room, _ = found
        else:
            room = next((r for r in self._rooms() if r.get("area_id") == area_id), None)
            if room is None:
                return False
        vac = self.vacuum(room)
        if not vac:
            return False
        state = self.states.get(key) if key else None
        nobody = not self.anyone_home()
        if nobody:
            await self._alarm("alarm_arm_home")
        try:
            await self.hass.services.async_call("vacuum", "start", {ATTR_ENTITY_ID: vac}, blocking=True)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Vacuum %s could not start", vac)
            if state:
                state.last_note = "start_failed"
            async_dispatcher_send(self.hass, SIGNAL_VACUUM_UPDATED)
            return False
        self.runs[vac] = {"area_id": area_id, "key": key, "alarm_changed": nobody, "started": dt_util.utcnow()}
        if state:
            state.waiting_until = None
            state.last_run = dt_util.utcnow()
            state.last_note = None
        self.sync()  # track the vacuum until the run is over
        return True

    async def _alarm(self, service: str) -> None:
        alarm = self.hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ALARM_ENTITY)
        if not alarm:
            return
        wanted = {"alarm_arm_home": "armed_home", "alarm_arm_away": "armed_away"}[service]
        if (st := self.hass.states.get(alarm)) is not None and st.state == wanted:
            return
        _LOGGER.debug("Vacuum: %s on %s", service, alarm)
        try:
            await self.hass.services.async_call("alarm_control_panel", service, {ATTR_ENTITY_ID: alarm}, blocking=True)
        except Exception as err:  # noqa: BLE001 - e.g. the panel needs a code
            _LOGGER.warning("Vacuum: could not %s %s: %s", service, alarm, err)

    # ── state changes: schedules, persons, vacuums ─────────────────────────

    @callback
    def _on_change(self, event: Event) -> None:
        entity_id = event.data.get("entity_id", "")
        old, new = event.data.get("old_state"), event.data.get("new_state")
        if new is None:
            return
        if entity_id.startswith(("person.", "alarm_control_panel.")):
            self._start_waiting()
        elif entity_id in self.runs and new.state in DONE and (old is None or old.state not in DONE):
            self.hass.async_create_task(self._run_over(entity_id))

    @callback
    def _start_waiting(self) -> None:
        """Somebody came home or left, or the alarm changed: start waiting
        moments whose conditions are met now."""
        now = dt_util.now()
        for key, state in self.states.items():
            if state.waiting_until is None:
                continue
            found = self.find(key)
            if found is None or not found[1].get(CONF_VACUUM_ENABLED, True):
                state.waiting_until = None
                continue
            if state.waiting_until < now:
                state.waiting_until = None
                state.last_note = self.blocked(found[2]) or "not_allowed"
                continue
            if self.blocked(found[2]) is None:
                state.waiting_until = None  # start once
                self.hass.async_create_task(self.start_clean(key))

    async def _run_over(self, vac: str) -> None:
        """The vacuum is docked/idle again: nobody home → Armed Away."""
        run = self.runs.pop(vac, None)
        if run is None:
            return
        if run.get("area_id"):
            self.last_clean[run["area_id"]] = dt_util.utcnow().isoformat()
            await self._store.async_save({"last_clean": self.last_clean})
            async_dispatcher_send(self.hass, SIGNAL_VACUUM_UPDATED)
        if self.anyone_home():
            _LOGGER.debug("Vacuum %s done; somebody home, alarm left alone", vac)
        else:
            await self._alarm("alarm_arm_away")
        self.sync()

    # ── on/off per room ────────────────────────────────────────────────────

    def rooms_with_vacuum(self) -> list[str]:
        return [r["area_id"] for r in self._rooms() if self.vacuum(r)]

    def enabled(self, area_id: str) -> bool:
        room = next((r for r in self._rooms() if r.get("area_id") == area_id), None)
        return bool((room or {}).get(CONF_VACUUM_ENABLED, True))

    async def set_enabled(self, area_id: str, enabled: bool) -> None:
        from . import _async_save  # here: avoids an import cycle

        rooms = [
            {**r, CONF_VACUUM_ENABLED: enabled} if r.get("area_id") == area_id else r
            for r in self._rooms()
        ]
        await _async_save(self.hass, rooms=rooms)

    # ── for the panel ──────────────────────────────────────────────────────

    def plan_info(self, area_id: str) -> dict[str, Any]:
        out = {}
        for key, state in self.states.items():
            if key.startswith(f"{area_id}:"):
                out[key.partition(":")[2]] = {
                    "next": state.next.isoformat() if state.next else None,
                    "waiting_until": state.waiting_until.isoformat() if state.waiting_until else None,
                    "last_run": state.last_run.isoformat() if state.last_run else None,
                    "note": state.last_note,
                }
        return out
