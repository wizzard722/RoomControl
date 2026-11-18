"""Switch platform: a "Dim" switch on every room device (the room's 1% mode)."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .clocks import SIGNAL_CLOCKS_UPDATED, clock_key, room_clocks
from .entity_ids import with_roomcontrol_ids
from .const import (
    ALARM_DISARMED,
    DOMAIN,
    DUSK_ELEVATION_DEFAULT,
    SETTING_DUSK_ELEVATION,
    SETTING_SUN_ENTITY,
    GENERAL_DEVICE,
    SETTING_ALARM_ENTITY,
    SETTING_LATE_HOME_PERSONS,
    SETTING_VACATION_FOLLOWS_ALARM,
    SIGNAL_CONFIG_UPDATED,
    SIGNAL_LATE_HOME,
    SIGNAL_VACATION,
)
from .rooms import all_dim_rooms, managed_areas, room_lights, stored_room
from .slots import hm_minutes, mode_slots, slot_part
from .announce import CONF_ANNOUNCE_OFF, announce_rooms
from .const import CONF_MEDIA_PLAYERS


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_dim"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Keep one Dim switch per room that has lamps."""
    async_add_entities = with_roomcontrol_ids(hass, "switch", async_add_entities)
    entities: dict[str, RoomDimSwitch] = {}

    @callback
    def _sync(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {
            room["area_id"]
            for room in hass.data.get(DOMAIN, {}).get("rooms", [])
            if room.get("area_id") in areas and room_lights(hass, room["area_id"])
        }
        new = [RoomDimSwitch(a) for a in wanted - entities.keys()]
        for entity in new:
            entities[entity.area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(entities.keys() - wanted):
            del entities[area_id]
            if entity_id := ent_reg.async_get_entity_id("switch", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync))

    # One on/off switch per alarm clock.
    clocks: dict[str, ClockSwitch] = {}

    @callback
    def _sync_clocks(*_: Any) -> None:
        areas = managed_areas(hass)
        wanted = {clock_key(a, c["id"]) for a, c in room_clocks(hass) if a in areas}
        new = [ClockSwitch(k) for k in wanted - clocks.keys()]
        for entity in new:
            clocks[entity.key] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key in list(clocks.keys() - wanted):
            del clocks[key]
            if entity_id := ent_reg.async_get_entity_id("switch", DOMAIN, _clock_unique_id(key)):
                ent_reg.async_remove(entity_id)

    _sync_clocks()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_clocks))

    # The former "Stofzuigschema" switches (cleaning moments on/off per room)
    # are gone: each moment has its own on/off. Remove leftover entities.
    ent_reg = er.async_get(hass)
    for entity in list(er.async_entries_for_config_entry(ent_reg, entry.entry_id)):
        if entity.domain == "switch" and entity.unique_id.startswith(f"{DOMAIN}_") and entity.unique_id.endswith("_vacuum"):
            ent_reg.async_remove(entity.entity_id)

    # Per lock: "op slot als niemand thuis" and "sluittijden" (Configuratie).
    locks: dict[tuple[str, str, str], LockOptionSwitch] = {}

    @callback
    def _sync_locks(*_: Any) -> None:
        from .lock import wanted_locks

        wanted = {(a, e, opt) for (a, e) in wanted_locks(hass) for opt in LOCK_OPTIONS}
        new = [LockOptionSwitch(a, e, opt) for (a, e, opt) in wanted - locks.keys()]
        for entity in new:
            locks[(entity.area_id, entity.target, entity.option)] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for key in list(locks.keys() - wanted):
            del locks[key]
            if entity_id := ent_reg.async_get_entity_id("switch", DOMAIN, _lock_unique_id(*key)):
                ent_reg.async_remove(entity_id)

    _sync_locks()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_locks))

    # One "Omroepen" switch per room with media players (Configuratie).
    announce: dict[str, AnnounceSwitch] = {}

    @callback
    def _sync_announce(*_: Any) -> None:
        wanted = set(announce_rooms(hass))
        new = [AnnounceSwitch(a) for a in wanted - announce.keys()]
        for entity in new:
            announce[entity.area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(announce.keys() - wanted):
            del announce[area_id]
            if entity_id := ent_reg.async_get_entity_id("switch", DOMAIN, _announce_unique_id(area_id)):
                ent_reg.async_remove(entity_id)

    _sync_announce()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_announce))

    # One "Vakantie" switch for the whole house, on the General device.
    async_add_entities([VacationSwitch()])

    # One "Alles dim" switch for the whole house, on the General device.
    async_add_entities([AllDimSwitch()])

    # One "Later thuis" switch per chosen person, on the General device.
    late: dict[str, LateHomeSwitch] = {}

    @callback
    def _sync_late(*_: Any) -> None:
        settings = hass.data.get(DOMAIN, {}).get("settings", {})
        wanted = {p for p in settings.get(SETTING_LATE_HOME_PERSONS, []) or [] if p}
        new = [LateHomeSwitch(p) for p in wanted - late.keys()]
        for entity in new:
            late[entity.person] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for person in list(late.keys() - wanted):
            del late[person]
            hass.data.get(DOMAIN, {}).setdefault("late_home_active", set()).discard(person)
            if entity_id := ent_reg.async_get_entity_id("switch", DOMAIN, _late_unique_id(person)):
                ent_reg.async_remove(entity_id)
        async_dispatcher_send(hass, SIGNAL_LATE_HOME)

    _sync_late()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_late))


class RoomDimSwitch(SwitchEntity):
    """The room's 1% mode: on = lamps that are on go to 1%, lamps that go on burn at 1%."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:brightness-4"
    _attr_name = "Dim"
    _attr_entity_category = EntityCategory.CONFIG  # "Configuratie" on the device page

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self._attr_unique_id = _unique_id(area_id)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, area_id)})
        self._watching: str | None = None
        self._unsub: CALLBACK_TYPE | None = None

    def _room_light(self) -> Any:
        return self.hass.data.get(DOMAIN, {}).get("entities", {}).get(self.area_id)

    @callback
    def _refresh(self, *_: Any) -> None:
        light = self._room_light()
        # Follow the room's light: its state changes when the 1% mode changes.
        entity_id = getattr(light, "entity_id", None)
        if entity_id != self._watching:
            if self._unsub:
                self._unsub()
            self._watching = entity_id
            self._unsub = async_track_state_change_event(self.hass, [entity_id], self._refresh) if entity_id else None
        self._attr_available = light is not None
        self._attr_is_on = bool(light is not None and light.dimmed)
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        if (light := self._room_light()) is not None:
            await light.async_set_dim(True)
        self._refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if (light := self._room_light()) is not None:
            await light.async_set_dim(False)
        self._refresh()


SETTING_ALL_DIM_SLOTS = "all_dim_slots"  # time slots, same format as a light bundle's
SETTING_ALL_DIM_WINDOW = "all_dim_window"  # older: one {"start", "end"} window, every day
SETTING_ALL_DIM_FOLLOWS_ALARM = "all_dim_follows_alarm"  # disarmed → all back


def all_dim_slots(hass: HomeAssistant) -> list[dict[str, Any]]:
    """The time slots in which "Alles dim" is on by itself (an older single
    window counts as one slot on every day)."""
    settings = hass.data.get(DOMAIN, {}).get("settings", {})
    slots = settings.get(SETTING_ALL_DIM_SLOTS)
    if isinstance(slots, list):
        return [x for x in slots if isinstance(x, dict)]
    window = settings.get(SETTING_ALL_DIM_WINDOW)
    if isinstance(window, dict) and hm_minutes(window.get("start")) is not None and hm_minutes(window.get("end")) is not None:
        return [{"days": [0, 1, 2, 3, 4, 5, 6], "start": {"type": "time", "time": window["start"]},
                 "end": {"type": "time", "time": window["end"]}}]
    return []


def _sun_phase(hass: HomeAssistant) -> tuple[str, bool]:
    """("light" | "dusk" | "dark", sun down) from the sun entity of the settings."""
    settings = hass.data.get(DOMAIN, {}).get("settings", {})
    sun = hass.states.get(settings.get(SETTING_SUN_ENTITY) or "sun.sun")
    if sun is not None and sun.state == "below_horizon":
        return "dark", True
    elevation = sun.attributes.get("elevation") if sun is not None else None
    limit = settings.get(SETTING_DUSK_ELEVATION, DUSK_ELEVATION_DEFAULT)
    if isinstance(elevation, (int, float)) and isinstance(limit, (int, float)) and elevation < limit:
        return "dusk", False
    return "light", False


def all_dim_active(hass: HomeAssistant) -> bool:
    """One of the All dim time slots runs now (vacation slots in vacation mode)."""
    slots = mode_slots(all_dim_slots(hass), bool(hass.data.get(DOMAIN, {}).get("vacation")))
    if not slots:
        return False
    phase, sun_down = _sun_phase(hass)
    now = dt_util.now()
    return any(slot_part(slot, now, phase, sun_down) is not None for slot in slots)


class AllDimSwitch(SwitchEntity):
    """All rooms (with lamps, not hidden) in 1% mode at once — the "Alles dim"
    button of the panel. On when every one of those rooms is dimmed.

    With a time window (general settings) it switches on by itself when the
    window starts and off when it ends; in between it can still be switched
    by hand. "Follows the alarm": when the alarm goes to disarmed, all back."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:brightness-4"
    _attr_name = "Alles dim"
    _attr_unique_id = f"{DOMAIN}_all_dim"

    def __init__(self) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
        )
        self._watching: list[str] = []
        self._unsub: CALLBACK_TYPE | None = None
        self._window: tuple[int, int] | None = None
        self._window_unsubs: list[CALLBACK_TYPE] = []
        self._in_window: bool | None = None
        self._alarm_unsub: CALLBACK_TYPE | None = None
        self._alarm_watching: str | None = None

    def _room_lights(self) -> list[Any]:
        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        return [e for a in all_dim_rooms(self.hass) if (e := entities.get(a)) is not None and e.follows_dim]

    @callback
    def _refresh(self, *_: Any) -> None:
        lights = self._room_lights()
        # Follow the room lights: their state changes when the 1% mode changes.
        watch = sorted(e.entity_id for e in lights if e.entity_id)
        if watch != self._watching:
            if self._unsub:
                self._unsub()
            self._watching = watch
            self._unsub = async_track_state_change_event(self.hass, watch, self._refresh) if watch else None
        self._attr_available = bool(lights)
        self._attr_is_on = bool(lights) and all(e.dimmed for e in lights)
        self._attr_extra_state_attributes = {
            "dimmed_rooms": sorted(e._area_id for e in lights if e.dimmed),
            "time_slots": len(all_dim_slots(self.hass)),
            "time_slot_active": bool(self._in_window),
        }
        if self.entity_id:
            self.async_write_ha_state()

    @callback
    def _on_config(self, *_: Any) -> None:
        self._refresh()
        self._setup_window()
        self._setup_alarm()

    @callback
    def _setup_alarm(self) -> None:
        settings = self.hass.data.get(DOMAIN, {}).get("settings", {})
        alarm = settings.get(SETTING_ALARM_ENTITY) if settings.get(SETTING_ALL_DIM_FOLLOWS_ALARM) else None
        if alarm == self._alarm_watching:
            return
        if self._alarm_unsub:
            self._alarm_unsub()
            self._alarm_unsub = None
        self._alarm_watching = alarm or None
        if alarm:
            self._alarm_unsub = async_track_state_change_event(self.hass, [alarm], self._on_alarm)

    @callback
    def _on_alarm(self, event: Any) -> None:
        """The alarm goes to disarmed (from any other settled state): all back."""
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if new is None or new.state != ALARM_DISARMED or old is None or old.state == ALARM_DISARMED:
            return
        if any(e.dimmed for e in self._room_lights()):
            self.hass.async_create_task(self._set(False))

    @callback
    def _setup_window(self) -> None:
        """Check the time slots every minute (and now); act when one starts or ends."""
        wanted = bool(all_dim_slots(self.hass))
        if wanted and not self._window_unsubs:
            self._window_unsubs.append(async_track_time_interval(self.hass, self._window_tick, timedelta(minutes=1)))
        elif not wanted and self._window_unsubs:
            for unsub in self._window_unsubs:
                unsub()
            self._window_unsubs = []
        self._window_tick()

    @callback
    def _window_tick(self, _now: Any = None) -> None:
        """Only a change counts: a slot starts → all dim, the last one ends → all back.
        In between the user may switch it by hand."""
        inside = all_dim_active(self.hass)
        previous, self._in_window = self._in_window, inside
        if inside and not previous:
            self.hass.async_create_task(self._set(True))
        elif previous and not inside:
            self.hass.async_create_task(self._set(False))
        elif self.entity_id:
            self._refresh()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self._setup_window()
        self._setup_alarm()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._on_config))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        for unsub in self._window_unsubs:
            unsub()
        self._window_unsubs = []
        if self._alarm_unsub:
            self._alarm_unsub()
            self._alarm_unsub = None

    async def _set(self, dim: bool) -> None:
        for light in self._room_lights():
            await light.async_set_dim(dim)
        self._refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


def _clock_unique_id(key: str) -> str:
    return f"{DOMAIN}_clock_{key.replace(':', '_')}_enabled"


class ClockSwitch(SwitchEntity):
    """An alarm clock on or off; attributes say when it goes off next."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:alarm"
    _attr_entity_category = EntityCategory.CONFIG  # "Configuratie" on the device page

    def __init__(self, key: str) -> None:
        self.key = key
        self._attr_unique_id = _clock_unique_id(key)

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.key.partition(":")[0])})

    def _manager(self) -> Any:
        return self.hass.data.get(DOMAIN, {}).get("clocks")

    def _clock(self) -> dict[str, Any] | None:
        manager = self._manager()
        found = manager.find(self.key) if manager else None
        return found[2] if found else None

    @property
    def name(self) -> str:
        clock = self._clock() or {}
        return f"Wekker {(clock.get('name') or '').strip() or clock.get('time', '')}".strip()

    @property
    def is_on(self) -> bool:
        return bool((self._clock() or {}).get("enabled", True))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        manager = self._manager()
        state = manager.states.get(self.key) if manager else None
        clock = self._clock() or {}
        return {
            "time": clock.get("time"),
            "days": clock.get("days", []),
            "next_ring": state.next.isoformat() if state and state.next else None,
            "ringing": bool(state and state.ringing),
            "snoozed_until": state.snoozed_until.isoformat() if state and state.snoozed_until else None,
            "step": state.step if state else 0,
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CLOCKS_UPDATED, self.async_write_ha_state))
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.async_write_ha_state))

    async def async_turn_on(self, **kwargs: Any) -> None:
        if manager := self._manager():
            await manager.set_enabled(self.key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if manager := self._manager():
            await manager.set_enabled(self.key, False)


# ── "Omroepen" per room ─────────────────────────────────────────────────────


def _announce_unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}_announce"


class AnnounceSwitch(SwitchEntity):
    """The room's speakers take part in announcements (Omroepen). Off: none
    of them; per speaker it can be set in the panel."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:bullhorn-outline"
    _attr_name = "Omroepen"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self._attr_unique_id = _announce_unique_id(area_id)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    def _players(self) -> list[str]:
        return [p for p in (stored_room(self.hass, self.area_id) or {}).get(CONF_MEDIA_PLAYERS, []) or [] if p]

    @property
    def is_on(self) -> bool:
        off = set((stored_room(self.hass, self.area_id) or {}).get(CONF_ANNOUNCE_OFF, []) or [])
        return any(p not in off for p in self._players())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        off = set((stored_room(self.hass, self.area_id) or {}).get(CONF_ANNOUNCE_OFF, []) or [])
        return {"speakers": [p for p in self._players() if p not in off]}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.async_write_ha_state))

    async def _set(self, on: bool) -> None:
        from . import _async_save  # here: avoids an import cycle

        rooms = []
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == self.area_id:
                room = {k: v for k, v in room.items() if k != CONF_ANNOUNCE_OFF}
                if not on:
                    room[CONF_ANNOUNCE_OFF] = self._players()
            rooms.append(room)
        await _async_save(self.hass, rooms=rooms)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


# ── "Vakantie" for the whole house, on the General device ──────────────────


class VacationSwitch(RestoreEntity, SwitchEntity):
    """Vacation: bundles' time slots "only during vacation" run, those "not
    during vacation" don't (e.g. staying up later). Kept across restarts."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:palm-tree"
    _attr_name = "Vakantie"
    _attr_unique_id = f"{DOMAIN}_vacation"
    _attr_extra_state_attributes = {"roomcontrol_vacation": True}

    def __init__(self) -> None:
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
        )

    @property
    def is_on(self) -> bool:
        return bool(self.hass.data.get(DOMAIN, {}).get("vacation"))

    async def async_added_to_hass(self) -> None:
        last = await self.async_get_last_state()
        if last is not None and last.state == "on":
            self._set(True)
        self._unsub_alarm: CALLBACK_TYPE | None = None
        self._watch_alarm()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._watch_alarm))
        self.async_on_remove(self._stop_watching)

    # Follow the alarm (setting): Armed Vacation → vacation on, leaving it → off.

    def _settings(self) -> dict[str, Any]:
        return self.hass.data.get(DOMAIN, {}).get("settings", {})

    @callback
    def _stop_watching(self) -> None:
        if self._unsub_alarm:
            self._unsub_alarm()
            self._unsub_alarm = None

    @callback
    def _watch_alarm(self, *_: Any) -> None:
        self._stop_watching()
        alarm = self._settings().get(SETTING_ALARM_ENTITY)
        if not alarm or not self._settings().get(SETTING_VACATION_FOLLOWS_ALARM):
            return
        self._unsub_alarm = async_track_state_change_event(self.hass, [alarm], self._on_alarm)
        st = self.hass.states.get(alarm)
        if st is not None and st.state == "armed_vacation" and not self.is_on:
            self._set(True)  # already armed for vacation when the option was switched on

    @callback
    def _on_alarm(self, event: Any) -> None:
        new, old = event.data.get("new_state"), event.data.get("old_state")
        if new is None or new.state in ("arming", "pending", "unavailable", "unknown"):
            return
        if new.state == "armed_vacation" and not self.is_on:
            self._set(True)
        elif new.state != "armed_vacation" and old is not None and old.state == "armed_vacation" and self.is_on:
            self._set(False)

    @callback
    def _set(self, on: bool) -> None:
        self.hass.data.setdefault(DOMAIN, {})["vacation"] = on
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_VACATION)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._set(False)


# ── "Later thuis" (home later) per person, on the General device ─────────────


def _late_unique_id(person: str) -> str:
    return f"{DOMAIN}_late_home_{person.replace('.', '_')}"


def late_home_active(hass: HomeAssistant) -> set[str]:
    """Persons whose "Later thuis" switch is on."""
    return set(hass.data.get(DOMAIN, {}).setdefault("late_home_active", set()))


class LateHomeSwitch(RestoreEntity, SwitchEntity):
    """Someone comes home later: rooms set for it keep their bundles on.

    Can only be switched on while the person is not home; goes off by itself
    as soon as they come home."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:home-clock-outline"

    def __init__(self, person: str) -> None:
        self.person = person
        self._attr_unique_id = _late_unique_id(person)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, GENERAL_DEVICE)}, name="Generiek", manufacturer="RoomControl"
        )
        self._unsub: CALLBACK_TYPE | None = None

    @property
    def name(self) -> str:
        st = self.hass.states.get(self.person) if self.hass else None
        who = (st.attributes.get("friendly_name") if st else None) or self.person.split(".", 1)[-1]
        return f"Later thuis {who}"

    def _active(self) -> set[str]:
        return self.hass.data.setdefault(DOMAIN, {}).setdefault("late_home_active", set())

    @property
    def is_on(self) -> bool:
        return self.person in self._active()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        st = self.hass.states.get(self.person)
        return {"person": self.person, "person_home": bool(st and st.state == "home")}

    def _home(self) -> bool:
        st = self.hass.states.get(self.person)
        return st is not None and st.state == "home"

    async def async_added_to_hass(self) -> None:
        last = await self.async_get_last_state()
        if last is not None and last.state == "on" and not self._home():
            self._active().add(self.person)
            async_dispatcher_send(self.hass, SIGNAL_LATE_HOME)  # rooms pick it up after a restart
        self._unsub = async_track_state_change_event(self.hass, [self.person], self._on_person)
        self.async_on_remove(self._unsub)

    @callback
    def _on_person(self, _event: Any) -> None:
        if self._home() and self.person in self._active():
            # Home now: the switch goes off and the held rooms may go off.
            self._set(False)
        else:
            self.async_write_ha_state()

    @callback
    def _set(self, on: bool) -> None:
        active = self._active()
        if on:
            active.add(self.person)
        else:
            active.discard(self.person)
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_LATE_HOME)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self._home():
            raise HomeAssistantError(f"{self.name}: {self.person} is thuis; 'Later thuis' kan alleen als de persoon weg is")
        self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._set(False)


# option key → (name suffix, icon, default)
LOCK_OPTIONS = {
    "away_lock": ("op slot als niemand thuis", "mdi:home-lock", False),
    "slots_enabled": ("sluittijden", "mdi:lock-clock", True),
}


def _lock_unique_id(area_id: str, entity_id: str, option: str) -> str:
    return f"{DOMAIN}_{area_id}_lock_{entity_id.partition('.')[2]}_{option}"


class LockOptionSwitch(SwitchEntity):
    """One option of a lock: lock when nobody is home / its lock times."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG  # "Configuratie" on the device page

    def __init__(self, area_id: str, target: str, option: str) -> None:
        self.area_id = area_id
        self.target = target
        self.option = option
        self._attr_unique_id = _lock_unique_id(area_id, target, option)
        self._attr_icon = LOCK_OPTIONS[option][1]

    @property
    def device_info(self) -> DeviceInfo:
        """On the room's device."""
        return DeviceInfo(identifiers={(DOMAIN, self.area_id)})

    def _manager(self) -> Any:
        return self.hass.data.get(DOMAIN, {}).get("locks")

    def _lock(self) -> dict[str, Any]:
        manager = self._manager()
        found = manager.find(self.area_id, self.target) if manager else None
        return found[1] if found else {}

    @property
    def name(self) -> str:
        state = self.hass.states.get(self.target) if self.hass else None
        lock_name = (state.attributes.get("friendly_name") if state else None) or self.target
        return f"{lock_name} – {LOCK_OPTIONS[self.option][0]}"

    @property
    def is_on(self) -> bool:
        return bool(self._lock().get(self.option, LOCK_OPTIONS[self.option][2]))

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self.async_write_ha_state))

    async def _set(self, value: bool) -> None:
        if manager := self._manager():
            await manager.set_option(self.area_id, self.target, {self.option: value})

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)
