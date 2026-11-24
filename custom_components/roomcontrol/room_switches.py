"""Switches that belong to a room (espresso machine, fridge, freezer, TV …).

Room option "switches": [{"entity_id": "switch.x" | "remote.x" (e.g. an
NVIDIA Shield), "may_off": bool (default
True), "off_on": ["all_off", "nobody_home", "smoke"], "back_on": bool
(default True: after "nobody home", back on when someone is home again)}].

A switch that may go off is switched off by RoomControl at the moments
chosen for it (default: All off, nobody home and smoke):
- "all_off":     the room's All off (its RoomControl light switched off);
- "nobody_home": nobody home: the alarm goes to Armed Away (without an alarm
                 panel: the last person leaves); back on at Disarmed or
                 Armed Home (someone comes home);
- "room_away":   every person linked to the room (room → Motion &
                 presence) has left the house, also while others are still
                 home; back on when one of them is home again (with back_on);
- "night":       the night: the alarm goes to Armed Home (people asleep);
                 back on at Disarmed (with back_on);
- "slot":        during the switch's own time slots ("slots", the light-bundle
                 slot format, Normal / Leave / Vacation), back on when the
                 slot ends (with back_on);
- "smoke":       a smoke alarm (back on at All safe, see smoke.py);
- "vacation_home" / "vacation_away": while vacation at home / elsewhere is
                 on (switch.py "Vakantie"); back on when it ends or changes
                 to a kind the switch is not set for.
A switch that may never go off ("may_off": false) is never switched off by
RoomControl, also not by the smoke action's own list of switches.
"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SETTING_ALARM_ENTITY, SIGNAL_CONFIG_UPDATED, SIGNAL_VACATION
from .rooms import anyone_home, household_persons, managed_areas, room_persons

_LOGGER = logging.getLogger(__name__)

CONF_SWITCHES = "switches"
IDLE_BACK_OFF = 30  # minutes at standby before a switch turned on by hand during its slot goes off again
OFF_MOMENTS = ("all_off", "nobody_home", "room_away", "night", "slot", "smoke", "vacation_home", "vacation_away")
DEFAULT_OFF_ON = ["all_off", "nobody_home", "smoke"]
SWITCH_DOMAINS = ("switch.", "remote.")  # what a room's Switches may hold
CONF_MEDIA_OFF_AWAY = "media_off_away"  # room option: media players off when nobody is home
MEDIA_IDLE = ("off", "standby", "unavailable", "unknown")


async def async_turn(hass: HomeAssistant, entities: list[str], on: bool) -> None:
    """Switch these on / off, each with its own domain (switch, remote)."""
    by_domain: dict[str, list[str]] = {}
    for entity in entities:
        by_domain.setdefault(entity.split(".", 1)[0], []).append(entity)
    for domain, ids in by_domain.items():
        await hass.services.async_call(domain, "turn_on" if on else "turn_off", {ATTR_ENTITY_ID: ids}, blocking=True)


def room_switches(room: dict[str, Any] | None) -> list[dict[str, Any]]:
    """The room's switches, with their defaults filled in."""
    out = []
    for item in (room or {}).get(CONF_SWITCHES, []) or []:
        if not isinstance(item, dict) or not str(item.get("entity_id", "")).startswith(SWITCH_DOMAINS):
            continue
        off_on = item.get("off_on")
        out.append({
            "entity_id": item["entity_id"],
            "may_off": item.get("may_off", True) is not False,
            "back_on": item.get("back_on", True) is not False,
            "off_on": list(dict.fromkeys("nobody_home" if m == "armed_away" else m for m in off_on if m in (*OFF_MOMENTS, "armed_away")))
            if isinstance(off_on, list) else list(DEFAULT_OFF_ON),
            "slots": [x for x in item.get("slots") or [] if isinstance(x, dict)],
        })
    return out


@callback
def switches_for(hass: HomeAssistant, moment: str, area_id: str | None = None) -> list[str]:
    """Switches that go off at this moment (in one room, or in every room)."""
    managed = managed_areas(hass)
    out: list[str] = []
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        area = room.get("area_id")
        if area not in managed or (area_id is not None and area != area_id):
            continue
        for sw in room_switches(room):
            if sw["may_off"] and moment in sw["off_on"] and sw["entity_id"] not in out:
                out.append(sw["entity_id"])
    return out


@callback
def never_off(hass: HomeAssistant) -> set[str]:
    """Switches that RoomControl may never switch off, in any room."""
    return {
        sw["entity_id"]
        for room in hass.data.get(DOMAIN, {}).get("rooms", [])
        for sw in room_switches(room)
        if not sw["may_off"]
    }


@callback
def log_switches(hass: HomeAssistant, switches: list[str], kind: str, reason: str) -> None:
    """Note it in each room's "What happened" (the room light's log)."""
    entities = hass.data.get(DOMAIN, {}).get("entities", {})
    for room in hass.data.get(DOMAIN, {}).get("rooms", []):
        own = {sw["entity_id"] for sw in room_switches(room)} | set(room.get("media_players", []) or [])
        mine = [s for s in switches if s in own]
        light = entities.get(room.get("area_id"))
        if not mine or light is None or not hasattr(light, "_debug"):
            continue
        names = [((st := hass.states.get(s)) and st.attributes.get("friendly_name")) or s for s in mine]
        light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": kind, "reason": reason,
                             "bundles": names, "items": mine})


async def async_switch_off(hass: HomeAssistant, switches: list[str], why: str) -> None:
    """Switch these off (those that are on), never one that may not go off."""
    blocked = never_off(hass)
    todo = [s for s in switches if s not in blocked and (st := hass.states.get(s)) is not None and st.state == "on"]
    if not todo:
        return
    whys = hass.data.setdefault(DOMAIN, {}).setdefault("switch_why", {})
    for s in todo:
        whys[s] = why.replace(" ", "_")  # offpay.py: why it went off
    _LOGGER.debug("Room switches off (%s): %s", why, todo)
    log_switches(hass, todo, "off", f"switches_{why.replace(' ', '_')}")
    try:
        await async_turn(hass, todo, False)
    except Exception:  # noqa: BLE001
        _LOGGER.warning("Could not switch off %s (%s)", todo, why)


class RoomSwitches:
    """Nobody home: the chosen switches go off, and back on when someone is
    (each switch set to "back_on"; one set not to stays off).

    With an alarm panel (general settings): off at Armed Away, back on at
    Disarmed or Armed Home. Without one: off when the last person of the
    household leaves, back on when someone comes home. Only the switches
    RoomControl switched off go back on (kept across restarts)."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsubs: list[CALLBACK_TYPE] = []
        self._track: CALLBACK_TYPE | None = None
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.switches_off")
        self.switched_off: list[str] = []
        self.vacation_off: list[str] = []  # switched off for a vacation
        self.room_off: dict[str, list[str]] = {}  # area: switched off because the room's persons left
        self.night_off: list[str] = []  # switched off for the night (Armed Home)
        self.slot_off: list[str] = []  # switched off for one of their own time slots
        self._idle_since: dict[str, float] = {}
        self._track_rooms: CALLBACK_TYPE | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.switched_off = [s for s in data.get("off", []) if isinstance(s, str)]
        self.vacation_off = [s for s in data.get("vacation_off", []) if isinstance(s, str)]
        self.night_off = [s for s in data.get("night_off", []) if isinstance(s, str)]
        self.slot_off = [s for s in data.get("slot_off", []) if isinstance(s, str)]
        room_off = data.get("room_off") if isinstance(data.get("room_off"), dict) else {}
        self.room_off = {a: [s for s in v if isinstance(s, str)] for a, v in room_off.items() if isinstance(v, list)}

    def _keep(self) -> None:
        self._store.async_delay_save(lambda: {"off": self.switched_off, "vacation_off": self.vacation_off, "room_off": self.room_off,
                     "night_off": self.night_off, "slot_off": self.slot_off}, 1)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_VACATION, self._on_vacation))
        self._unsubs.append(async_track_time_interval(self.hass, self._slot_tick, timedelta(minutes=1)))
        self._sync()

    @callback
    def _on_vacation(self, *_: Any) -> None:
        self.hass.async_create_task(self.async_vacation())

    async def async_vacation(self) -> None:
        """Vacation changed: off what this kind of vacation switches off; back
        on what RoomControl switched off for a vacation that no longer applies
        (not while it is off because nobody is home)."""
        mode = self.hass.data.get(DOMAIN, {}).get("vacation")
        kind = ("home" if mode is True else mode) if mode else None
        wanted = set(switches_for(self.hass, f"vacation_{kind}")) if kind else set()
        blocked = never_off(self.hass)
        off = [
            s for s in wanted
            if s not in blocked and (st := self.hass.states.get(s)) is not None and st.state == "on"
        ]
        back = [s for s in self.vacation_off if s not in wanted and s not in self.switched_off
                and self.hass.states.get(s) is not None]
        if back and self.nobody_home():
            # Nobody home: what also goes off then stays off until someone is.
            away = set(switches_for(self.hass, "nobody_home"))
            hold = [s for s in back if s in away]
            self.switched_off = list(dict.fromkeys([*self.switched_off, *hold]))
            back = [s for s in back if s not in away]
        self.vacation_off = [s for s in dict.fromkeys([*self.vacation_off, *off]) if s in wanted]
        self._keep()
        if off:
            await async_switch_off(self.hass, sorted(off), f"vacation {kind}")
        if back:
            _LOGGER.debug("Room switches back on (vacation over): %s", back)
            log_switches(self.hass, back, "on", "switches_vacation_over")
            try:
                await async_turn(self.hass, back, True)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Could not switch %s back on (vacation over)", back)

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        if self._track:
            self._track()
            self._track = None
        if self._track_rooms:
            self._track_rooms()
            self._track_rooms = None

    def _alarm(self) -> str | None:
        return self.hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ALARM_ENTITY) or None

    @callback
    def _sync(self, *_: Any) -> None:
        if self._track:
            self._track()
            self._track = None
        alarm = self._alarm()
        ids = [alarm] if alarm else list(household_persons(self.hass))
        if ids:
            self._track = async_track_state_change_event(self.hass, ids, self._on_change)
        if self._track_rooms:
            self._track_rooms()
            self._track_rooms = None
        persons = sorted({p for _area, ps in self._away_rooms() for p in ps})
        if persons:
            self._track_rooms = async_track_state_change_event(self.hass, persons, self._on_room_person)

    def _away_rooms(self) -> list[tuple[str, list[str]]]:
        """(area, its persons) for rooms with a switch set to "room_away"."""
        managed = managed_areas(self.hass)
        out = []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            area = room.get("area_id")
            persons = room_persons(self.hass, room)
            if area in managed and persons and switches_for(self.hass, "room_away", area):
                out.append((area, persons))
        return out

    @callback
    def _on_room_person(self, event: Event) -> None:
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if new is None or old is None or (new.state == "home") == (old.state == "home"):
            return
        person = event.data["entity_id"]
        for area, persons in self._away_rooms():
            if person not in persons:
                continue
            if new.state == "home":
                self.hass.async_create_task(self.async_room_back(area))
            elif not any((st := self.hass.states.get(p)) is not None and st.state == "home" for p in persons):
                self.hass.async_create_task(self.async_room_away(area))

    @callback
    def _slot_tick(self, _now: Any = None) -> None:
        """Switches with the moment "slot": off while one of their slots runs, back on after."""
        from .slots import mode_slots, slot_part  # noqa: PLC0415
        from .switch import _sun_phase  # noqa: PLC0415

        phase, sun_down = _sun_phase(self.hass)
        now = dt_util.as_local(dt_util.now())
        vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
        managed = managed_areas(self.hass)
        off, back = [], []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") not in managed:
                continue
            for sw in room_switches(room):
                entity = sw["entity_id"]
                if not sw["may_off"] or "slot" not in sw["off_on"]:
                    if entity in self.slot_off:
                        self.slot_off.remove(entity)
                    continue
                active = any(slot_part(x, now, phase, sun_down) is not None for x in mode_slots(sw["slots"], vacation))
                st = self.hass.states.get(entity)
                if active and entity not in self.slot_off and st is not None and st.state == "on":
                    off.append(entity)
                elif active and entity in self.slot_off and st is not None and st.state == "on":
                    # Switched on by hand during the slot: on until it has been idle IDLE_BACK_OFF, then off again.
                    if self._idle_minutes(room.get("area_id"), entity) >= IDLE_BACK_OFF:
                        self.slot_off.remove(entity)
                        off.append(entity)
                elif not active and entity in self.slot_off:
                    self.slot_off.remove(entity)
                    if sw["back_on"] and entity not in self.switched_off and entity not in self.vacation_off:
                        back.append(entity)
        if off:
            self.slot_off.extend(off)
            self.hass.async_create_task(async_switch_off(self.hass, off, "slot"))
        if back:
            log_switches(self.hass, back, "on", "switches_slot_over")
            self.hass.async_create_task(async_turn(self.hass, back, True))
        if off or back:
            self._keep()

    def _idle_minutes(self, area: str | None, entity: str) -> float:
        """How long the switch's device has been at standby (its power meter);
        0 while in use or without a meter."""
        learning = self.hass.data.get(DOMAIN, {}).get("device_learning")
        learner = learning.learners.get(f"{area}|switch:{entity}") if learning else None
        if learner is None or learner.last is None:
            return 0.0
        idle = self._idle_since
        t, w = learner.last
        now = dt_util.utcnow().timestamp()
        if learner.run is not None or w > learner.threshold():
            idle.pop(entity, None)
            return 0.0
        return (now - idle.setdefault(entity, now)) / 60

    async def async_night(self) -> None:
        """Armed Home (the night): the "night" switches off, remembering which were on."""
        todo = [
            s for s in switches_for(self.hass, "night")
            if s not in never_off(self.hass) and (st := self.hass.states.get(s)) is not None and st.state == "on"
        ]
        if not todo:
            return
        self.night_off = list(dict.fromkeys([*self.night_off, *todo]))
        self._keep()
        await async_switch_off(self.hass, todo, "night")

    async def async_night_back(self) -> None:
        """Disarmed (up again): back on what went off for the night (set to come back on)."""
        todo, self.night_off = self.night_off, []
        if not todo:
            return
        self._keep()
        stay_off = {
            sw["entity_id"]
            for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            for sw in room_switches(room)
            if not sw["back_on"]
        }
        todo = [s for s in todo if self.hass.states.get(s) is not None and s not in stay_off
                and s not in self.vacation_off and s not in self.switched_off]
        if not todo:
            return
        log_switches(self.hass, todo, "on", "switches_night_over")
        try:
            await async_turn(self.hass, todo, True)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not switch %s back on (night over)", todo)

    async def async_room_away(self, area: str) -> None:
        """The room's persons all left: its "room_away" switches off."""
        todo = [
            s for s in switches_for(self.hass, "room_away", area)
            if s not in never_off(self.hass) and (st := self.hass.states.get(s)) is not None and st.state == "on"
        ]
        if not todo:
            return
        self.room_off[area] = list(dict.fromkeys([*self.room_off.get(area, []), *todo]))
        self._keep()
        await async_switch_off(self.hass, todo, "room away")

    async def async_room_back(self, area: str) -> None:
        """One of the room's persons is home again: back on what went off for it
        (not what is off because nobody is home or for a vacation)."""
        todo = self.room_off.pop(area, [])
        if not todo:
            return
        self._keep()
        stay_off = {
            sw["entity_id"]
            for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            for sw in room_switches(room)
            if not sw["back_on"]
        }
        todo = [s for s in todo if self.hass.states.get(s) is not None and s not in stay_off
                and s not in self.vacation_off and s not in self.switched_off]
        if not todo:
            return
        _LOGGER.debug("Room switches back on (room person home): %s", todo)
        log_switches(self.hass, todo, "on", "switches_room_back")
        try:
            await async_turn(self.hass, todo, True)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not switch %s back on (room person home)", todo)

    @callback
    def _on_change(self, event: Event) -> None:
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if new is None or old is None or new.state == old.state:
            return
        if event.data["entity_id"].startswith("person."):
            if old.state == "home" and not anyone_home(self.hass):
                self.hass.async_create_task(self.async_away("nobody home"))
            elif new.state == "home":
                self.hass.async_create_task(self.async_back("someone home"))
        elif self.hass.data.get(DOMAIN, {}).get("vacuum_alarm_hold"):
            return  # the vacuum disarmed it for a run while nobody is home: nothing changes
        elif new.state == "armed_away":
            self.hass.async_create_task(self.async_away("armed away"))
        elif new.state in ("disarmed", "armed_home"):
            self.hass.async_create_task(self.async_back(new.state))
        if not event.data["entity_id"].startswith("person.") and not self.hass.data.get(DOMAIN, {}).get("vacuum_alarm_hold"):
            if new.state == "armed_home":
                self.hass.async_create_task(self.async_night())
            elif new.state == "disarmed":
                self.hass.async_create_task(self.async_night_back())

    def nobody_home(self) -> bool:
        """Armed Away (with an alarm panel), else nobody of the household home."""
        if alarm := self._alarm():
            if hold := self.hass.data.get(DOMAIN, {}).get("vacuum_alarm_hold"):
                return hold == "armed_away"
            st = self.hass.states.get(alarm)
            return st is not None and st.state == "armed_away"
        return bool(household_persons(self.hass)) and not anyone_home(self.hass)

    async def async_media_off(self, why: str) -> None:
        """Nobody home: the media players of rooms set to "media_off_away" off."""
        from .const import CONF_MEDIA_PLAYERS  # noqa: PLC0415

        managed = managed_areas(self.hass)
        players = [
            p for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            if room.get("area_id") in managed and room.get(CONF_MEDIA_OFF_AWAY)
            for p in room.get(CONF_MEDIA_PLAYERS, []) or []
            if p and (st := self.hass.states.get(p)) is not None and st.state not in MEDIA_IDLE
        ]
        if not players:
            return
        _LOGGER.debug("Media players off (%s): %s", why, players)
        log_switches(self.hass, players, "off", "media_nobody_home")
        try:
            await self.hass.services.async_call("media_player", "turn_off", {ATTR_ENTITY_ID: players}, blocking=True)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not switch media players %s off (%s)", players, why)

    async def async_away(self, why: str) -> None:
        """Nobody home: off, remembering which were on."""
        await self.async_media_off(why)
        todo = [
            s for s in switches_for(self.hass, "nobody_home")
            if s not in never_off(self.hass) and (st := self.hass.states.get(s)) is not None and st.state == "on"
        ]
        if not todo:
            return
        self.switched_off = list(dict.fromkeys([*self.switched_off, *todo]))
        self._keep()
        await async_switch_off(self.hass, todo, why)

    async def async_back(self, why: str) -> None:
        """Someone home again: what RoomControl switched off goes back on."""
        todo, self.switched_off = self.switched_off, []
        self._keep()
        # Only the switches set to come back on (a switch set to stay off stays off).
        stay_off = {
            sw["entity_id"]
            for room in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            for sw in room_switches(room)
            if not sw["back_on"]
        }
        todo = [s for s in todo if self.hass.states.get(s) is not None and s not in stay_off
                and s not in self.vacation_off]
        if not todo:
            return
        _LOGGER.debug("Room switches back on (%s): %s", why, todo)
        log_switches(self.hass, todo, "on", "switches_back")
        try:
            await async_turn(self.hass, todo, True)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Could not switch %s back on (%s)", todo, why)
