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
 "notify": "notify.mobile_app_x", "notify_skip": entity (on → no messages),
 "code": "1234" (optional, for panels that need one),
 "screen": {"title": text entity, "text": text entity},   # e.g. an NSPanel
 "lamps": {"lights": [...], "selects": [...], "presets": {state: option},
           "motion": [sensors], "off_minutes": 10},       # status lamps (WLED)
 "states": {state: {"screen_title", "screen_text", "screen_clear": s,
            "speak": text, "players": [...], "volume": %, "volume_after": %,
            "repeat": s (0: once), "siren": url, "siren_players": [...],
            "stop_media": [players], "notify": text}}}

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
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .announce import announce_tts
from .const import ALARM_TRANSITIONAL, DOMAIN, SETTING_ALARM_ENTITY, SIGNAL_CONFIG_UPDATED
from .slots import mode_slots, slot_part

_LOGGER = logging.getLogger(__name__)

ARMED = ("armed_home", "armed_away", "armed_night", "armed_vacation", "armed_custom_bypass")
SERVICE_FOR = {
    "armed_home": "alarm_arm_home",
    "armed_away": "alarm_arm_away",
    "armed_night": "alarm_arm_night",
    "armed_vacation": "alarm_arm_vacation",
    "disarmed": "alarm_disarm",
}
KEEP_LAMPS_ON = ("pending", "triggered")
FAIL_AFTER = timedelta(minutes=5)


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
        self._fail_timer: CALLBACK_TYPE | None = None
        self._screen_timer: CALLBACK_TYPE | None = None
        self._lamps_timer: CALLBACK_TYPE | None = None
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
        for name in ("_track", "_away_timer", "_rearm_timer", "_fail_timer", "_screen_timer", "_lamps_timer"):
            if (unsub := getattr(self, name)) is not None:
                unsub()
                setattr(self, name, None)
        if self._loop:
            self._loop.cancel()

    @callback
    def _sync(self, *_: Any) -> None:
        cfg = self.cfg()
        ids = [self.panel(), *self.persons(), *self.distance_sensors().values(), *((cfg.get("lamps") or {}).get("motion") or [])]
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
        if entity_id in ((cfg.get("lamps") or {}).get("motion") or []) and new.state in ("on", "detected"):
            self.hass.async_create_task(self._lamps_show(self.state()))

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
        elif self.cfg().get("outside", "disarm") == "disarm" and self.anyone_home() and self.state() in ARMED:
            self.hass.async_create_task(self.set_state("disarmed", "slot_end"))

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
            return
        if self._away_active or self._away_timer is not None:
            return

        @callback
        def _go(_now: Any) -> None:
            self._away_timer = None
            if self.all_away():
                self._away_active = True
                self.hass.async_create_task(self._away())

        self._away_timer = async_call_later(self.hass, _num(cfg.get("away_delay"), 1) * 60, _go)

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

    @callback
    def _arrived(self, person: str) -> None:
        cfg = self.cfg()
        self._away_active = False
        if not cfg.get("home_on", True) or self.state() not in ARMED:
            return
        name = self._name(person)
        slot = self.slot_now()
        minutes = int(_num(cfg.get("home_minutes"), 10))
        self.hass.async_create_task(self.set_state("disarmed", f"home:{name}"))
        if slot and minutes > 0:
            self._notify(f"{name} komt thuis. Alarm is uitgeschakeld voor {minutes} minuten.")
            if self._rearm_timer:
                self._rearm_timer()

            @callback
            def _again(_now: Any) -> None:
                self._rearm_timer = None
                again = self.slot_now()
                if again and self.state() == "disarmed":
                    self.hass.async_create_task(self.set_state(again["state"], "rearm"))

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
        self._loop = self.hass.async_create_background_task(self._run_state(new), f"{DOMAIN}_alarm_{new}")

    async def _run_state(self, state: str) -> None:
        st = (self.cfg().get("states") or {}).get(state) or {}
        await self._screen(st.get("screen_title"), st.get("screen_text"), _num(st.get("screen_clear"), 0))
        await self._lamps_show(state)
        if stop := [p for p in st.get("stop_media") or [] if p]:
            await self._call("media_player", "media_stop", {ATTR_ENTITY_ID: stop})
        if st.get("notify"):
            self._notify(st["notify"])
        speak, players = st.get("speak"), [p for p in st.get("players") or [] if p]
        siren, siren_players = st.get("siren"), [p for p in st.get("siren_players") or [] if p]
        if not (speak and players) and not (siren and siren_players):
            return
        if players and isinstance(st.get("volume"), (int, float)):
            await self._call("media_player", "volume_set", {ATTR_ENTITY_ID: players, "volume_level": st["volume"] / 100})
        repeat = _num(st.get("repeat"), 0)
        try:
            while True:
                if siren and siren_players:
                    await self._call("media_player", "play_media", {
                        ATTR_ENTITY_ID: siren_players, "media_content_id": siren, "media_content_type": "music"})
                if speak and players and (tts := announce_tts(self.hass)):
                    await self._call("tts", "speak", {
                        ATTR_ENTITY_ID: tts, "media_player_entity_id": players, "message": speak, "cache": True})
                if repeat <= 0 or self.state() != state:
                    break
                await asyncio.sleep(max(5, repeat))
                if self.state() != state:
                    break
        finally:
            if players and isinstance(st.get("volume_after"), (int, float)):
                await self._call("media_player", "volume_set", {
                    ATTR_ENTITY_ID: players, "volume_level": st["volume_after"] / 100})

    async def _screen(self, title: Any, text: Any, clear: float) -> None:
        screen = self.cfg().get("screen") or {}
        if not text:
            return
        if title_entity := screen.get("title"):
            await self._set_text(title_entity, str(title or ""))
        if text_entity := screen.get("text"):
            await self._set_text(text_entity, str(text) if title_entity or not title else f"{title}: {text}")
        if self._screen_timer:
            self._screen_timer()
            self._screen_timer = None
        if clear > 0:
            @callback
            def _clear(_now: Any) -> None:
                self._screen_timer = None
                for entity in (screen.get("title"), screen.get("text")):
                    if entity:
                        self.hass.async_create_task(self._set_text(entity, ""))

            self._screen_timer = async_call_later(self.hass, clear, _clear)

    async def _set_text(self, entity_id: str, value: str) -> None:
        domain = entity_id.split(".", 1)[0]
        if domain not in ("text", "input_text"):
            return
        await self._call(domain, "set_value", {ATTR_ENTITY_ID: entity_id, "value": value})

    async def _lamps_show(self, state: str | None) -> None:
        """Status lamps: the preset of this state, on; off again after a while
        (not while a sensor went off or the alarm sounds)."""
        lamps = self.cfg().get("lamps") or {}
        lights, selects = [x for x in lamps.get("lights") or [] if x], [x for x in lamps.get("selects") or [] if x]
        if not state or not (lights or selects):
            return
        preset = (lamps.get("presets") or {}).get(state)
        if preset:
            for select in selects:
                await self._call("select", "select_option", {ATTR_ENTITY_ID: select, "option": preset})
        if lights:
            await self._call("light", "turn_on", {ATTR_ENTITY_ID: lights})
        if self._lamps_timer:
            self._lamps_timer()
            self._lamps_timer = None
        minutes = _num(lamps.get("off_minutes"), 10)
        if lights and minutes > 0 and state not in KEEP_LAMPS_ON:
            @callback
            def _off(_now: Any) -> None:
                self._lamps_timer = None
                if self.state() not in KEEP_LAMPS_ON:
                    self.hass.async_create_task(self._call("light", "turn_off", {ATTR_ENTITY_ID: lights}))

            self._lamps_timer = async_call_later(self.hass, minutes * 60, _off)

    async def test_state(self, state: str) -> None:
        """Panel "Test": screen, status lamps and one spoken message of this state."""
        st = (self.cfg().get("states") or {}).get(state) or {}
        await self._screen(st.get("screen_title"), st.get("screen_text"), _num(st.get("screen_clear"), 30) or 30)
        await self._lamps_show(state)
        players = [p for p in st.get("players") or [] if p]
        if st.get("speak") and players and (tts := announce_tts(self.hass)):
            await self._call("tts", "speak", {ATTR_ENTITY_ID: tts, "media_player_entity_id": players, "message": st["speak"]})

    # ── helpers ────────────────────────────────────────────────────────────

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - one broken device must not stop the rest
            _LOGGER.warning("Alarm: %s.%s failed: %s", domain, service, err)

    @callback
    def _notify(self, message: str) -> None:
        cfg = self.cfg()
        service = cfg.get("notify") or ""
        skip = cfg.get("notify_skip")
        if not service.startswith("notify.") or (skip and (st := self.hass.states.get(skip)) is not None and st.state == "on"):
            return
        self._log("notify", message)
        self.hass.async_create_task(self._call(
            "notify", service.split(".", 1)[1], {"title": "Alarm Systeem", "message": message}))

    @callback
    def _log(self, what: str, detail: str = "") -> None:
        self.log.appendleft({"at": dt_util.utcnow().isoformat(), "what": what, "detail": detail})

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
            "log": list(self.log)[:15],
        }
