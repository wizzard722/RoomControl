"""Alarm: RoomControl puts the alarm panel in the right state and acts per state.

General setting "alarm" (panel → Alarm), with the house's alarm panel from
"alarm_entity":

{"slots_on": bool, "slots": [time slot + {"state": armed_home | armed_away |
   armed_night | armed_vacation | disarmed, "only_away": bool}],
 "outside": "disarm" | "none",          # when the last slot ends
 "away_on": bool, (who counts: the persons of Presence in the general settings),
 "away_delay": minutes, "distance_sensors": {person: sensor (m, km or mi)}
 (older: "distance_sensor", one sensor for everyone),
 "distance_km": 100, "far_state": "armed_vacation", "near_state": "armed_home",
 "locks": [lock ids] (locked first), "fail_notify": bool,
 "home_on": bool, "home_minutes": 10,   # someone comes home: disarm (re-arm a slot later)
 "home_lights": bool,                    # ... and when dark: the "Later thuis" rooms' lamps
                                         # on until home_minutes have passed
 "notify": "notify.mobile_app_x", "notify_skip": entity (on → no messages),
 "code": "1234" (optional, for panels that need one),
 "states": {state: {"text": text (spoken and/or sent), "speak_on": bool, "notify_on": bool,
            "speak_rooms": [area ids], "volume": %, "volume_after": %, "repeat": s (0: once),
            "stop": bool, "stop_rooms": [area ids], "notify_persons": [...], "notify_ha": bool,
            "lamps": [{"entity_id": light, "preset": WLED preset name (optional)}]}}}
 A state's lamps go on (a WLED strip with its preset) when the state starts;
 lamps of the previous state that the new state does not use go off.
 (older: "speak" and "notify" texts per state, see resolve_state)
Speakers are the media players set per room (room → Media); no rooms chosen
means every room that has them. (Older: "players" and "stop_media" lists
of players are still used when no rooms are set.)

Slots, "everyone away" and the distance are judged when they change (a slot
starting or ending, the last person leaving, the distance crossing the
limit), so a state set by hand in between is left alone.
"""
from __future__ import annotations

import asyncio
import json
from collections import deque
from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from homeassistant.components import persistent_notification

from .announce import announce_tts
from .person_notify import person_notify_service
from .const import (
    ALARM_TRANSITIONAL,
    CONF_MEDIA_PLAYERS,
    DOMAIN,
    SETTING_ALARM_ENTITY,
    SETTING_SUN_ENTITY,
    SIGNAL_CONFIG_UPDATED,
    SIGNAL_LATE_HOME,
)
from .rooms import managed_areas
from .slots import hm_minutes, mode_slots, slot_part

_LOGGER = logging.getLogger(__name__)

ARMED = ("armed_home", "armed_away", "armed_night", "armed_vacation", "armed_custom_bypass")
SERVICE_FOR = {
    "armed_home": "alarm_arm_home",
    "armed_away": "alarm_arm_away",
    "armed_night": "alarm_arm_night",
    "armed_vacation": "alarm_arm_vacation",
    "disarmed": "alarm_disarm",
}
FAIL_AFTER = timedelta(minutes=5)

# What each state does until the user changes it (texts in Dutch or English,
# after Home Assistant's language). Every state has a text; "speak_on" /
# "notify_on" say whether it is spoken / sent by default. A value the user
# set, also an empty one, replaces the default.
_DEFAULT_STATES = {
    "nl": {
        "arming": ("Alarm Systeem wordt ingeschakeld.", True, False),
        "pending": ("Alarm Systeem is geactiveerd.", True, True),
        "triggered": ("Het Alarm Systeem is afgegaan.", True, True),
        "disarmed": ("Alarm Systeem is uitgeschakeld.", False, False),
        "armed_home": ("Alarm Systeem staat op Armed Home.", False, False),
        "armed_away": ("Armed Away is ingeschakeld.", False, True),
        "armed_night": ("Alarm Systeem staat op Armed Night.", False, False),
        "armed_vacation": ("Alarm Systeem staat op Armed Vacation.", False, False),
    },
    "en": {
        "arming": ("The alarm system is being armed.", True, False),
        "pending": ("The alarm system has been activated.", True, True),
        "triggered": ("The alarm system has gone off.", True, True),
        "disarmed": ("The alarm system is disarmed.", False, False),
        "armed_home": ("The alarm system is set to Armed Home.", False, False),
        "armed_away": ("Armed Away is on.", False, True),
        "armed_night": ("The alarm system is set to Armed Night.", False, False),
        "armed_vacation": ("The alarm system is set to Armed Vacation.", False, False),
    },
}
# Older versions: a spoken and a message text per state. Only used to carry
# over a state the user changed then (resolve_state).
_LEGACY_TEXTS = {
    "nl": {
        "arming": {"speak": "Alarm Systeem wordt ingeschakeld."},
        "pending": {"speak": "Alarm Systeem is geactiveerd.",
                    "notify": "Het Alarm Systeem heeft gedetecteerd dat een sensor is afgegaan."},
        "triggered": {"speak": "Het Alarm Systeem is afgegaan.", "notify": "Het alarm gaat af!"},
        "armed_away": {"notify": "Armed Away is ingeschakeld."},
    },
    "en": {
        "arming": {"speak": "The alarm system is being armed."},
        "pending": {"speak": "The alarm system has been activated.",
                    "notify": "The alarm system detected that a sensor went off."},
        "triggered": {"speak": "The alarm system has gone off.", "notify": "The alarm is going off!"},
        "armed_away": {"notify": "Armed Away is on."},
    },
}
_DEFAULT_SOUND = {
    "arming": {"volume": 30, "volume_after": 20, "repeat": 0},
    "pending": {"volume": 40, "volume_after": 20, "repeat": 10},
    "triggered": {"volume": 40, "volume_after": 20, "repeat": 10},
}


def state_defaults(language: str | None) -> dict[str, dict[str, Any]]:
    """The default settings of every alarm state: text, speak_on, notify_on,
    the sound settings, and ("legacy") the texts of older versions."""
    lang = "nl" if (language or "").lower().startswith("nl") else "en"
    out = {}
    for state, (text, speak_on, notify_on) in _DEFAULT_STATES[lang].items():
        out[state] = {**_DEFAULT_SOUND.get(state, {}), "text": text, "speak_on": speak_on,
                      "notify_on": notify_on, "legacy": _LEGACY_TEXTS[lang].get(state, {})}
    return out


def resolve_state(default: dict[str, Any], own: dict[str, Any]) -> dict[str, Any]:
    """One text per state, spoken and/or sent as a message:
    {"text", "speak_on", "notify_on", ...}. Older settings had a
    spoken text ("speak") and a message text ("notify"): the spoken text
    becomes the text (else the message text) and each channel is on when it
    had a text. "speak"/"notify" in the result are what is actually spoken /
    sent ("" = nothing), so the rest of the code reads those."""
    legacy = default.get("legacy") or {}
    if "text" not in own and ("speak" in own or "notify" in own):
        # Changed in an older version: carry its spoken / message text over.
        speak = own.get("speak", legacy.get("speak", "")) or ""
        notify = own.get("notify", legacy.get("notify", "")) or ""
        text, speak_on, notify_on = speak or notify, bool(speak), bool(notify)
    else:
        text = own.get("text", default.get("text", "")) or ""
        speak_on, notify_on = bool(default.get("speak_on")), bool(default.get("notify_on"))
    out = {k: v for k, v in {**default, **own}.items() if k != "legacy"}
    out["text"] = text
    out["speak_on"] = own["speak_on"] if isinstance(own.get("speak_on"), bool) else speak_on
    out["notify_on"] = own["notify_on"] if isinstance(own.get("notify_on"), bool) else notify_on
    out["speak"] = out["text"] if out["speak_on"] else ""
    out["notify"] = out["text"] if out["notify_on"] else ""
    return out


def _num(value: Any, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) else default


class AlarmAutomation:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.log: deque[dict[str, Any]] = deque(maxlen=40)
        self._unsubs: list[CALLBACK_TYPE] = []
        self._track: CALLBACK_TYPE | None = None
        self._tracked: tuple[str, ...] = ()
        self._slot_prev: str | None | bool = False  # False: not judged yet; None: apply what runs now
        self._slots_sig: str | None = None  # the time slots as last seen (changed → apply now)
        self._started = False
        self._away_timer: CALLBACK_TYPE | None = None
        self._away_active = False
        self._rearm_timer: CALLBACK_TYPE | None = None
        self._rearm_at: Any = None
        self._rearm_from: Any = None
        self._rearm_who: list[str] = []
        self._away_at: Any = None
        self._fail_timer: CALLBACK_TYPE | None = None
        self._loop: asyncio.Task | None = None

    # ── config ─────────────────────────────────────────────────────────────

    def cfg(self) -> dict[str, Any]:
        value = self.hass.data.get(DOMAIN, {}).get("settings", {}).get("alarm")
        return value if isinstance(value, dict) else {}

    def panel(self) -> str | None:
        return self.hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_ALARM_ENTITY) or None

    def state(self) -> str | None:
        st = self.hass.states.get(self.panel()) if self.panel() else None
        return st.state if st is not None else None

    def persons(self) -> list[str]:
        """Who counts: the persons of Presence (general settings); none chosen
        there means everyone, as there: every person in Home Assistant."""
        presence = [p for p in self.hass.data.get(DOMAIN, {}).get("settings", {}).get("persons", []) or [] if p]
        return presence or sorted(self.hass.states.async_entity_ids("person"))

    def anyone_home(self) -> bool:
        return any((st := self.hass.states.get(p)) is not None and st.state == "home" for p in self.persons())

    def all_away(self) -> bool:
        persons = self.persons()
        return bool(persons) and all(
            (st := self.hass.states.get(p)) is not None and st.state not in ("home", "unknown", "unavailable")
            for p in persons
        )

    def _sensor_km(self, sensor: str | None) -> float | None:
        """A distance sensor's value in km (None: no sensor or no number)."""
        st = self.hass.states.get(sensor) if sensor else None
        try:
            value = float(st.state) if st is not None else None
        except (TypeError, ValueError):
            return None
        if value is None:
            return None
        unit = (st.attributes.get("unit_of_measurement") or "km").lower()
        return value / 1000 if unit == "m" else value * 1.609344 if unit in ("mi", "miles") else value

    def auto_distance_sensor(self, person: str) -> str | None:
        """The distance sensor Home Assistant's Proximity integration made for
        this person (sensor.<zone>_<person>_distance), if there is one."""
        name = person.split(".", 1)[1]
        found = [
            e for e in self.hass.states.async_entity_ids("sensor")
            if e.endswith(f"_{name}_distance") or e == f"sensor.{name}_distance"
        ]
        return sorted(found)[0] if found else None

    def distance_sensors(self) -> dict[str, str]:
        """Person → distance sensor: chosen here (an older single sensor counts
        for everyone), else the person's Proximity sensor."""
        own = {p: s for p, s in (self.cfg().get("distance_sensors") or {}).items() if s}
        if not own and (legacy := self.cfg().get("distance_sensor")):
            own = {p: legacy for p in self.persons()}
        for person in self.persons():
            if person not in own and (auto := self.auto_distance_sensor(person)):
                own[person] = auto
        return own

    def distances(self) -> dict[str, float | None]:
        """Each counted person's distance to home in km (None: not known)."""
        sensors = self.distance_sensors()
        return {p: self._sensor_km(sensors.get(p)) for p in self.persons()}

    def distance_km(self) -> float | None:
        """The distance that decides: the closest person. A person whose
        distance is not known is taken to be within the limit (0 km)."""
        values = self.distances()
        if not values:
            return None
        return min(0.0 if v is None else v for v in values.values())

    def _name(self, entity_id: str) -> str:
        st = self.hass.states.get(entity_id)
        return (st.attributes.get("friendly_name") if st else None) or entity_id

    # ── lifecycle ──────────────────────────────────────────────────────────

    @callback
    def start(self) -> None:
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))
        self._unsubs.append(async_at_started(self.hass, self._on_started))
        self._sync()

    @callback
    def _on_started(self, _hass: Any = None) -> None:
        """Home Assistant has started: a time slot running now puts the alarm
        in its state right away."""
        self._started = True
        self._slot_prev = None
        self._tick()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []
        for name in ("_track", "_away_timer", "_rearm_timer", "_fail_timer"):
            if (unsub := getattr(self, name)) is not None:
                unsub()
                setattr(self, name, None)
        if self._loop:
            self._loop.cancel()
        self.arrive_lights().clear()  # no dispatch: the rooms are going away too

    @callback
    def _sync(self, *_: Any) -> None:
        cfg = self.cfg()
        ids = [self.panel(), *self.persons(), *self.distance_sensors().values()]
        ids = tuple(sorted({i for i in ids if i}))
        if ids != self._tracked:
            if self._track:
                self._track()
            self._tracked = ids
            self._track = async_track_state_change_event(self.hass, list(ids), self._on_change) if ids else None
        # Time slots configured or changed: check at once and apply a slot running now.
        sig = json.dumps([cfg.get("slots") or [], cfg.get("slots_on", True), self.panel()], sort_keys=True, default=str)
        if sig != self._slots_sig:
            if self._slots_sig is not None and self._started:
                self._slot_prev = None
            self._slots_sig = sig
        self._tick()

    # ── what changed ───────────────────────────────────────────────────────

    @callback
    def _on_change(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if new is None:
            return
        cfg = self.cfg()
        if entity_id == self.panel():
            if old is None or old.state != new.state:
                self._on_alarm(new.state, old.state if old else None)
            return
        if entity_id in self.persons():
            was_home = old is not None and old.state == "home"
            if new.state == "home" and not was_home and old is not None:
                self._arrived(entity_id)
            self._check_away()
            self._tick()
            return
        if entity_id in self.distance_sensors().values():
            self._distance_changed()
            return

    # ── time slots ─────────────────────────────────────────────────────────

    def slot_now(self) -> dict[str, Any] | None:
        """The time slot that decides the alarm's state now (None: none)."""
        cfg = self.cfg()
        if not cfg.get("slots_on", True):
            return None
        slots = mode_slots(cfg.get("slots") or [], bool(self.hass.data.get(DOMAIN, {}).get("vacation")))
        if not slots:
            return None
        from .switch import _sun_phase

        phase, sun_down = _sun_phase(self.hass)
        now = dt_util.as_local(dt_util.now())
        home = self.anyone_home()
        for slot in slots:
            if slot.get("state") in SERVICE_FOR and (not slot.get("only_away") or not home):
                if slot_part(slot, now, phase, sun_down) is not None:
                    return slot
        return None

    @callback
    def _tick(self, _now: Any = None) -> None:
        if not self.panel():
            return
        slot = self.slot_now()
        target = slot.get("state") if slot else None
        previous, self._slot_prev = self._slot_prev, target
        if previous is False or target == previous:
            return  # before Home Assistant has started, or nothing new
        if self._rearm_timer is not None:
            return  # someone just came home: the slot's state comes back after the grace
        if target:
            self.hass.async_create_task(self.set_state(target, f"slot:{slot.get('name') or ''}"))
        elif self.cfg().get("outside", "disarm") == "disarm" and self.state() in ARMED:
            # The last time slot ended. Someone home: disarmed, if the alarm is
            # still in the slot's state (a state set by hand meanwhile stays).
            # Nobody home (should not happen: then "everyone away" acted):
            # the state of "everyone away" (closer / further than the limit).
            if self.anyone_home():
                if self.state() == previous:
                    self.hass.async_create_task(self.set_state("disarmed", "slot_end"))
            elif self.cfg().get("away_on", True) and self.state() != (away := self.away_target()):
                self.hass.async_create_task(self.set_state(away, "slot_end_away"))

    # ── everyone away / distance ───────────────────────────────────────────

    @callback
    def _check_away(self) -> None:
        cfg = self.cfg()
        if not cfg.get("away_on", True) or not self.panel():
            return
        if not self.all_away():
            self._away_active = False
            if self._away_timer:
                self._away_timer()
                self._away_timer = None
                self._away_at = None
            return
        if self._away_active or self._away_timer is not None:
            return

        @callback
        def _go(_now: Any) -> None:
            self._away_timer = None
            self._away_at = None
            if self.all_away():
                self._away_active = True
                self.hass.async_create_task(self._away())

        delay = _num(cfg.get("away_delay"), 1) * 60
        self._away_at = dt_util.now() + timedelta(seconds=delay)
        self._away_timer = async_call_later(self.hass, delay, _go)

    def away_target(self) -> str:
        cfg = self.cfg()
        km = self.distance_km()
        far = km is not None and km > _num(cfg.get("distance_km"), 100)
        return (cfg.get("far_state") or "armed_vacation") if far else (cfg.get("near_state") or "armed_home")

    async def _away(self) -> None:
        locks = [lock for lock in self.cfg().get("locks") or [] if lock]
        if locks:
            try:
                await self.hass.services.async_call("lock", "lock", {ATTR_ENTITY_ID: locks}, blocking=True)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Alarm: could not lock %s", locks)
        await self.set_state(self.away_target(), "away")

    @callback
    def _distance_changed(self) -> None:
        """Everyone is away and the distance crosses the limit: the state goes along."""
        if not self._away_active or not self.all_away():
            return
        cfg = self.cfg()
        own = {cfg.get("far_state") or "armed_vacation", cfg.get("near_state") or "armed_home"}
        target = self.away_target()
        if self.state() in own and self.state() != target:
            self.hass.async_create_task(self.set_state(target, "distance"))

    # ── someone comes home ─────────────────────────────────────────────────

    def arrive_lights(self) -> set[str]:
        """Persons for whom the "Later thuis" rooms' lamps are on after coming home."""
        return self.hass.data.setdefault(DOMAIN, {}).setdefault("arrive_active", set())

    @callback
    def _arrive_lights(self, on: bool, person: str | None = None) -> None:
        """Lamps of the rooms set for "Later thuis" on (it is dark) or off again.
        The rooms do it the way they do for "Later thuis": on while it holds,
        off afterwards unless there is motion in the room."""
        active = self.arrive_lights()
        if on and person:
            active.add(person)
        elif not on and active:
            active.clear()
        else:
            return
        async_dispatcher_send(self.hass, SIGNAL_LATE_HOME)

    @callback
    def _arrived(self, person: str) -> None:
        cfg = self.cfg()
        self._away_active = False
        # Someone else came home a moment ago (the wait time is running): this
        # person joins, and the wait time starts again for everyone.
        joining = self._rearm_timer is not None
        if not cfg.get("home_on", True) or (self.state() not in ARMED and not joining):
            return
        from .switch import _sun_phase

        name = self._name(person)
        slot = self.slot_now()
        minutes = int(_num(cfg.get("home_minutes"), 10))
        lights = minutes > 0 and cfg.get("home_lights", True) and _sun_phase(self.hass)[1]
        if self.state() in ARMED:
            self.hass.async_create_task(self.set_state("disarmed", f"home:{name}"))
        else:
            self._log("home_join", name)
        if lights:
            self._log("arrive_lights", name)
            self._arrive_lights(True, person)
        if (slot or lights) and minutes > 0:
            if slot and joining:
                self._notify(f"{name} komt ook thuis. Alarm blijft nog {minutes} minuten uitgeschakeld.")
            elif slot:
                self._notify(f"{name} komt thuis. Alarm is uitgeschakeld voor {minutes} minuten.")
            else:
                self._notify(f"{name} komt thuis.")
            if self._rearm_timer:
                self._rearm_timer()

            @callback
            def _again(_now: Any) -> None:
                # Time is up: the lamps off again and the alarm to the
                # time slot's state (no slot: someone is home, stays disarmed).
                self._rearm_timer = None
                self._rearm_at = None
                self._rearm_who = []
                if self.arrive_lights():
                    self._log("arrive_lights_off")
                    self._arrive_lights(False)
                again = self.slot_now()
                if again and self.state() == "disarmed":
                    self.hass.async_create_task(self.set_state(again["state"], "rearm"))

            self._rearm_who = [*self._rearm_who, name] if joining and name not in self._rearm_who else (self._rearm_who if joining else [name])
            self._rearm_from = dt_util.now()
            self._rearm_at = self._rearm_from + timedelta(minutes=minutes)
            self._rearm_timer = async_call_later(self.hass, minutes * 60, _again)
        else:
            self._notify(f"{name} komt thuis.")

    # ── setting the state ──────────────────────────────────────────────────

    async def set_state(self, target: str, why: str) -> None:
        panel = self.panel()
        if not panel or target not in SERVICE_FOR or self.state() == target:
            return
        data: dict[str, Any] = {ATTR_ENTITY_ID: panel}
        if code := self.cfg().get("code"):
            data["code"] = str(code)
        self._log(f"set:{target}", why)
        try:
            await self.hass.services.async_call("alarm_control_panel", SERVICE_FOR[target], data, blocking=True)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Alarm: could not set %s to %s: %s", panel, target, err)
            self._log("set_failed", target)
        if target != "disarmed" and self.cfg().get("fail_notify", True):
            if self._fail_timer:
                self._fail_timer()

            @callback
            def _check(_now: Any, want: str = target) -> None:
                self._fail_timer = None
                if self.state() not in ARMED and self.state() not in ("arming", "pending", "triggered"):
                    self._log("arm_failed", want)
                    self._notify("Alarm Systeem heeft gefaald om het alarm in te schakelen!")

            self._fail_timer = async_call_later(self.hass, FAIL_AFTER.total_seconds(), _check)

    # ── per state ──────────────────────────────────────────────────────────

    @callback
    def _on_alarm(self, new: str, old: str | None) -> None:
        if new in ("unavailable", "unknown"):
            return
        self._log(f"state:{new}", old or "")
        if new in ARMED or new == "disarmed":
            if self._fail_timer and new in ARMED:
                self._fail_timer()
                self._fail_timer = None
        if self._loop:
            self._loop.cancel()
            self._loop = None
        # A background task: it may repeat for as long as the state lasts.
        self._loop = self.hass.async_create_background_task(self._run_state(new, old), f"{DOMAIN}_alarm_{new}")

    def room_players(self, rooms: list[str] | None) -> list[str]:
        """The media players of these rooms (room → Media); none: every room's."""
        managed = managed_areas(self.hass)
        chosen = {r for r in rooms or [] if r}
        players: list[str] = []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            area = room.get("area_id")
            if area not in managed or (chosen and area not in chosen):
                continue
            for player in room.get(CONF_MEDIA_PLAYERS, []) or []:
                if player and player not in players:
                    players.append(player)
        return players

    def _players(self, st: dict[str, Any], kind: str) -> list[str]:
        """Players for speak / stop of one state's settings."""
        legacy = {"speak": "players", "stop": "stop_media"}[kind]
        if f"{kind}_rooms" not in st and isinstance(st.get(legacy), list):
            return [p for p in st[legacy] if p]  # older: players chosen one by one
        if kind == "stop" and not st.get("stop"):
            return []
        return self.room_players(st.get(f"{kind}_rooms"))

    def state_cfg(self, state: str) -> dict[str, Any]:
        """A state's settings: the defaults, with what the user set over them,
        resolved to one text and on/off per channel (see resolve_state)."""
        own = (self.cfg().get("states") or {}).get(state) or {}
        return resolve_state(state_defaults(self.hass.config.language).get(state, {}), own)

    @staticmethod
    def state_lamps(st: dict[str, Any]) -> list[dict[str, Any]]:
        """A state's lamps: [{"entity_id", "preset"}]."""
        return [
            {"entity_id": l["entity_id"], "preset": l.get("preset") or None}
            for l in st.get("lamps") or []
            if isinstance(l, dict) and str(l.get("entity_id", "")).startswith("light.")
        ]

    def preset_select(self, light: str) -> str | None:
        """The preset select of a WLED light (on the same device), if any."""
        ent_reg = er.async_get(self.hass)
        entry = ent_reg.async_get(light)
        if entry is None or not entry.device_id:
            return None
        for other in er.async_entries_for_device(ent_reg, entry.device_id):
            if other.domain == "select" and (other.translation_key == "preset" or other.entity_id.endswith("_preset")):
                return other.entity_id
        return None

    async def _run_lamps(self, state: str, old: str | None) -> None:
        """This state's lamps on (with their preset); the previous state's
        lamps that this state does not use, off."""
        lamps = self.state_lamps(self.state_cfg(state))
        mine = {l["entity_id"] for l in lamps}
        if old and old != state:
            before = [l["entity_id"] for l in self.state_lamps(self.state_cfg(old)) if l["entity_id"] not in mine]
            if before:
                await self._call("light", "turn_off", {ATTR_ENTITY_ID: before})
        for lamp in lamps:
            select = self.preset_select(lamp["entity_id"]) if lamp["preset"] else None
            if select:
                # A WLED preset switches the strip on by itself.
                await self._call("select", "select_option", {ATTR_ENTITY_ID: select, "option": lamp["preset"]})
            else:
                await self._call("light", "turn_on", {ATTR_ENTITY_ID: lamp["entity_id"]})

    async def _run_state(self, state: str, old: str | None = None) -> None:
        await self._run_lamps(state, old)
        st = self.state_cfg(state)
        if stop := self._players(st, "stop"):
            await self._call("media_player", "media_stop", {ATTR_ENTITY_ID: stop})
        if st.get("notify"):
            self._notify(st["notify"], st)
        speak, players = st.get("speak"), self._players(st, "speak")
        if not (speak and players):
            return
        loud = players
        if loud and isinstance(st.get("volume"), (int, float)):
            await self._call("media_player", "volume_set", {ATTR_ENTITY_ID: loud, "volume_level": st["volume"] / 100})
        repeat = _num(st.get("repeat"), 0)
        try:
            while True:
                if tts := announce_tts(self.hass):
                    await self._call("tts", "speak", {
                        ATTR_ENTITY_ID: tts, "media_player_entity_id": players, "message": speak, "cache": True})
                if repeat <= 0 or self.state() != state:
                    break
                await asyncio.sleep(max(5, repeat))
                if self.state() != state:
                    break
        finally:
            if loud and isinstance(st.get("volume_after"), (int, float)):
                await self._call("media_player", "volume_set", {
                    ATTR_ENTITY_ID: loud, "volume_level": st["volume_after"] / 100})

    async def test_state(self, state: str) -> dict[str, Any]:
        """Panel "Test": this state's text, once: spoken (when speech is on)
        and sent as a message (when the message is on), all as set.
        Returns what happened, for the panel."""
        st = self.state_cfg(state)
        out: dict[str, Any] = {"text": bool(st.get("text"))}
        if st.get("speak_on") and st.get("text"):
            players = self._players(st, "speak")
            tts = announce_tts(self.hass)
            out["speak"] = {"players": len(players), "tts": bool(tts)}
            if players and tts:
                await self._call("tts", "speak", {ATTR_ENTITY_ID: tts, "media_player_entity_id": players, "message": st["text"]})
        if st.get("notify_on") and st.get("text"):
            sent = self._notify(st["text"], st, test=True)
            out["notify"] = {**sent, "services": [s.split(".", 1)[1].removeprefix("mobile_app_") for s in sent["services"]]}
        return out

    # ── helpers ────────────────────────────────────────────────────────────

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - one broken device must not stop the rest
            _LOGGER.warning("Alarm: %s.%s failed: %s", domain, service, err)

    @callback
    def _notify(self, message: str, st: dict[str, Any] | None = None, test: bool = False) -> dict[str, Any]:
        """A message to the chosen persons' devices and/or as a notification in
        Home Assistant. Per state ("notify_persons", "notify_ha") or else the
        alarm's own choice ("msg_persons": [] = every person who counts,
        "msg_ha": default on). Nothing to persons while "notify_skip" is on.
        Returns where it went: {"services", "ha", "skipped",
        "no_device": persons without a device}."""
        cfg, st = self.cfg(), st or {}
        persons = st.get("notify_persons")
        if not isinstance(persons, list):
            persons = cfg.get("msg_persons") if isinstance(cfg.get("msg_persons"), list) else None
        persons = [p for p in persons or [] if p] or self.persons()
        off = st.get("notify_persons_off") if isinstance(st.get("notify_persons_off"), bool) else cfg.get("msg_persons_off", False)
        if off:
            persons = []
        ha = st.get("notify_ha") if isinstance(st.get("notify_ha"), bool) else cfg.get("msg_ha", True)
        skip = cfg.get("notify_skip")
        skipped = bool(skip and (s := self.hass.states.get(skip)) is not None and s.state == "on")
        services: list[str] = []
        no_device: list[str] = []
        if not skipped:
            for person in persons:
                service = person_notify_service(self.hass, person)
                if not service:
                    no_device.append(self._name(person))
                elif service not in services:
                    services.append(service)
            if (legacy := cfg.get("notify") or "").startswith("notify.") and legacy not in services:
                services.append(legacy)  # older: one service for every message
        result = {"services": services, "ha": bool(ha), "skipped": skipped, "no_device": no_device}
        if not services and not ha:
            return result
        title = "Alarm Systeem (test)" if test else "Alarm Systeem"
        if not test:
            self._log("notify", message)
        for service in services:
            self.hass.async_create_task(self._call(
                "notify", service.split(".", 1)[1], {"title": title, "message": message}))
        if ha:
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=f"{DOMAIN}_alarm")
        return result

    @callback
    def _log(self, what: str, detail: str = "") -> None:
        self.log.appendleft({"at": dt_util.utcnow().isoformat(), "what": what, "detail": detail})

    def timer(self) -> dict[str, Any] | None:
        """The running "someone comes home" wait time, for the panel's countdown."""
        if self._rearm_timer is None or self._rearm_at is None:
            return None
        slot = self.slot_now()
        return {
            "from": self._rearm_from.isoformat() if self._rearm_from else None,
            "until": self._rearm_at.isoformat(),
            "who": ", ".join(self._rearm_who),
            "count": len(self._rearm_who),
            "lights": bool(self.arrive_lights()),
            "state": slot.get("state") if slot else None,
        }

    def upcoming(self, hours: int = 24) -> list[dict[str, Any]]:
        """What RoomControl expects the alarm to do in the next `hours`
        (panel "Straks"): time slots starting and ending, arming after
        everyone left and re-arming after someone came home.
        [{"at": iso, "kind": ..., "name": ..., "state": ...}], soonest first."""
        if not self.panel():
            return []
        cfg = self.cfg()
        now = dt_util.now()
        until = now + timedelta(hours=hours)
        events: list[tuple[Any, str, str, str | None]] = []
        settings = self.hass.data.get(DOMAIN, {}).get("settings", {})
        sun = self.hass.states.get(settings.get(SETTING_SUN_ENTITY) or "sun.sun")

        def sun_at(attr: str) -> Any:
            value = sun.attributes.get(attr) if sun is not None else None
            parsed = dt_util.parse_datetime(value) if isinstance(value, str) else None
            return dt_util.as_local(parsed) if parsed else None

        def at_time(hm: Any, day: Any) -> Any:
            minutes = hm_minutes(hm)
            if minutes is None:
                return None
            return day.replace(hour=minutes // 60, minute=minutes % 60, second=0, microsecond=0)

        def add(when: Any, kind: str, name: str, state: str | None) -> None:
            if when is not None and now <= when <= until:
                events.append((when, kind, name, state))

        home = self.anyone_home()
        if cfg.get("slots_on", True):
            vacation = bool(self.hass.data.get(DOMAIN, {}).get("vacation"))
            ends_to = None
            if cfg.get("outside", "disarm") == "disarm":
                ends_to = "disarmed" if home else (self.away_target() if cfg.get("away_on", True) else None)
            for slot in mode_slots(cfg.get("slots") or [], vacation):
                if slot.get("state") not in SERVICE_FOR or (slot.get("only_away") and home):
                    continue
                name = slot.get("name") or ""
                days = {d for d in slot.get("days", []) or [] if isinstance(d, int)}
                start, end = slot.get("start") or {}, slot.get("end") or {}
                for offset in (-1, 0, 1):
                    day = now + timedelta(days=offset)
                    if day.weekday() not in days:
                        continue
                    if start.get("type", "time") == "time":
                        begin = at_time(start.get("time"), day)
                    else:
                        begin = sun_at("next_dusk" if start.get("type") == "dusk" else "next_setting") if offset == 0 else None
                    add(begin, "slot_start", name, slot["state"])
                    if end.get("type") == "sunrise":
                        stop = sun_at("next_rising") if offset in (0, -1) else None
                    else:
                        stop = at_time(end.get("time"), day)
                        if stop is not None and begin is not None and stop <= begin:
                            stop += timedelta(days=1)
                    add(stop, "slot_end", name, ends_to)
        # A slot ending where another one starts: only the start counts.
        starts = {e[0].isoformat(timespec="minutes") for e in events if e[1] == "slot_start"}
        events = [e for e in events if e[1] != "slot_end" or e[0].isoformat(timespec="minutes") not in starts]
        if self._away_timer is not None and self._away_at is not None:
            add(self._away_at, "away", "", self.away_target())
        if self._rearm_timer is not None and self._rearm_at is not None:
            if self.arrive_lights():
                add(self._rearm_at, "arrive_lights_off", "", None)
            if slot := self.slot_now():
                add(self._rearm_at, "rearm", slot.get("name") or "", slot.get("state"))
        events.sort(key=lambda e: e[0])
        seen: set[tuple[str, str, str]] = set()
        out = []
        for when, kind, name, state in events:
            mark = (when.isoformat(timespec="minutes"), kind, name)
            if mark not in seen:
                seen.add(mark)
                out.append({"at": when.isoformat(), "kind": kind, "name": name, "state": state})
        return out[:8]

    def status(self) -> dict[str, Any]:
        """For the panel's Alarm page."""
        panel = self.panel()
        st = self.hass.states.get(panel) if panel else None
        slot = self.slot_now()
        return {
            "entity": panel,
            "state": st.state if st else None,
            "since": st.last_changed.isoformat() if st else None,
            "slot": {"name": slot.get("name") or "", "state": slot.get("state")} if slot else None,
            "distance_km": round(km, 1) if (km := self.distance_km()) is not None else None,
            "away_target": self.away_target(),
            "all_away": self.all_away(),
            "persons": [
                {"id": p, "name": self._name(p), "home": (s := self.hass.states.get(p)) is not None and s.state == "home",
                 "km": round(km, 1) if (km := self.distances().get(p)) is not None else None,
                 "sensor": self.distance_sensors().get(p), "auto_sensor": self.auto_distance_sensor(p)}
                for p in self.persons()
            ],
            "rearm_pending": self._rearm_timer is not None,
            "timer": self.timer(),
            "upcoming": self.upcoming(),
            "log": list(self.log)[:15],
            "defaults": state_defaults(self.hass.config.language),
        }
