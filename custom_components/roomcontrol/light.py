"""Light platform: one group-like light entity per Home Assistant area.

Each room light also runs the room's rules:
- time slots (tijdvakken) per bundle: the bundle goes on when a slot starts
  and off when it ends;
- motion (any of the room's or linked rooms' sensors, each within its own
  time window) turns the lights on (if dark enough and someone is home); they
  go off after the room's grace period (0-10 min, default 5) without motion,
  when motion turned them on;
- alarm: lights go off when the alarm goes from disarmed to armed_home;
- smart options (per room, see learn.py): a grace period that learns, media
  and "the last motion was here" keeping the lights on, a learned standard
  brightness, replaying past evenings when nobody is home, and notifications
  for unusual motion or lights left on.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components import persistent_notification
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util, slugify
from homeassistant.util.color import color_temperature_to_rgb
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)

from .entity_ids import with_roomcontrol_ids
from .const import (
    CONF_COVERS_CLOSE_AT,
    CONF_COVERS_OPEN_AT,
    CONF_COVERS_OPEN_TIME,
    DIM_LEVEL_DEFAULT,
    SETTING_DIM_LEVEL,
    DUSK_ELEVATION_DEFAULT,
    SETTING_DUSK_ELEVATION,
    GENERAL_DEVICE,
    CONF_LATE_HOME,
    SIGNAL_LATE_HOME,
    SIGNAL_VACATION,
    SIGNAL_LAST_MOTION,
    CONF_ADAPTIVE_GRACE,
    CONF_MEDIA_HOLD,
    CONF_MEDIA_PLAYERS,
    MEDIA_ACTIVE_STATES,
    CONF_LAST_MOTION_HOLD,
    LAST_MOTION_HOLD_MAX,
    CONF_LEARN_BRIGHTNESS,
    CONF_AWAY_REPLAY,
    CONF_ANOMALY_ALERTS,
    ANOMALY_LIGHTS_ON_HOURS,
    ALARM_ARMED_AWAY,
    CONF_AWAY_FOLLOW_SCHEDULE,
    LUX_CONTROL_MIN_BRIGHTNESS,
    LUX_CONTROL_START_PCT,
    SETTING_SUN_ENTITY,
    CONF_LUX_CONTROL_OFF_ALARM,
    CONF_FAN_MOTION,
    CONF_FAN_TEMP_MIN,
    CONF_FAN_TEMP_SENSOR,
    CONF_FAN_TEMP_SPEED,
    FAN_TEMP_HYSTERESIS,
    CONF_FAN_RUN_ON,
    FAN_RUN_ON_MAX,
    VERSION,
    ALARM_ARMED_HOME,
    ARMED_HOME_NO_MOTION,
    CONF_ARMED_HOME_MODE,
    ALARM_DISARMED,
    ALARM_TRANSITIONAL,
    CONF_ALARM_ENTITY,
    CONF_COVER_GROUPS,
    CONF_COVERS_FOLLOW,
    CONF_COVERS,
    CONF_DAYLIGHT_LIGHTS,
    CONF_DAYLIGHT_MAX_KELVIN,
    CONF_DAYLIGHT_MIN_KELVIN,
    CONF_DAYLIGHT_PREFER_RGB,
    DAYLIGHT_MAX_KELVIN,
    DAYLIGHT_MIN_KELVIN,
    KELVIN_COLOR_MODES,
    RGB_COLOR_MODES,
    CONF_DOOR_GROUPS,
    CONF_DOOR_SENSORS,
    CONF_DOOR_TURN_ON,
    CONF_GROUPS,
    CONF_LIGHTS_NAME,
    DOOR_OPEN_STATES,
    CONF_FIXED_LEVELS,
    CONF_FOLLOW_DAYLIGHT,
    DAYLIGHT_UPDATE_INTERVAL,
    SETTING_ALARM_ENTITY,
    CONF_SUN_ENTITY,
    CONF_TARGET_LUX,
    CONF_TARGET_LUX_ENABLED,
    CONF_DARK_LUX,
    CONF_DEFAULT_BRIGHTNESS,
    CONF_LUX_CONTROL,
    LUX_CONTROL_DEADBAND,
    LUX_CONTROL_INTERVAL,
    LUX_CONTROL_MAX_STEP,
    LUX_CONTROL_MIN_GAP,
    DOMAIN,
    CONF_MANUAL_DURATION,
    CONF_MOTION_OFF_DELAY,
    MANUAL_DURATION_DEFAULT,
    MANUAL_DURATION_MAX,
    MANUAL_DURATION_MIN,
    MOTION_OFF_DELAY,
    MOTION_OFF_DELAY_MAX,
    SIGNAL_CONFIG_UPDATED,
)
from .control import rc_call
from .fan_activity import FanActivity, FanKey, fan_activities, fan_key
from .learn import LearnStore
from .smoke import SIGNAL_SMOKE, smoke_active
from .clocks import SIGNAL_CLOCKS_UPDATED
from .texts import text
from .vacuums import SIGNAL_VACUUM_UPDATED
from .slots import hm_minutes, mode_slots, slot_part
from .devices import split_identifier
from .rooms import (
    daylight_kelvin,
    supports_kelvin,
    presence_allows,
    room_lights,
    room_locks,
    room_motion_sensors,
    room_lux,
    room_lux_sensors,
    group_motion_sensors,
    anyone_home,
    fan_group,
    household_persons,
    room_fan_steps,
    room_neighbours,
    motion_slots,
    room_fans,
    linked_group,
    managed_areas,
    room_persons,
    stored_room,
)

_LOGGER = logging.getLogger(__name__)

MOTION_ON_STATES = ("on", "detected")
# Lux model: at most this much brightness (of 255) per step once the gain is known.
LUX_MODEL_MAX_STEP = 128
# A hand-made brightness change counts once the lamp stayed there this long (s).
BRIGHT_SETTLE = 20
# At most one notification of a kind per room in this time.
ANOMALY_REPEAT = timedelta(hours=6)
# A lamp at this brightness (of 255) or lower reads as 0%: it goes off instead.
ZERO_BRIGHTNESS = 1


def _reads_zero(data: dict[str, Any]) -> bool:
    """Would a turn_on with this data leave the lamp on at 0%?"""
    if "brightness_pct" in data:
        return round(float(data["brightness_pct"])) <= 0
    if ATTR_BRIGHTNESS in data:
        return float(data[ATTR_BRIGHTNESS]) <= ZERO_BRIGHTNESS
    return False


def _lamp_modes(hass: HomeAssistant, entity_id: str) -> set[str]:
    state = hass.states.get(entity_id)
    return {str(m) for m in (state.attributes.get("supported_color_modes") or [])} if state else set()


def _colour_state(hass: HomeAssistant, lamps: list[str]) -> dict[str, Any]:
    """What a RoomControl light offers for colour, from its lamps: colour (HS)
    when any lamp can do colour, colour temperature when any lamp can do that
    (or colour), else brightness only; plus the current colour of a lamp that is on."""
    modes: set[str] = set()
    lo: list[int] = []
    hi: list[int] = []
    for e in lamps:
        m = _lamp_modes(hass, e)
        modes |= m
        st = hass.states.get(e)
        if st is not None and m & KELVIN_COLOR_MODES:
            if isinstance(v := st.attributes.get("min_color_temp_kelvin"), (int, float)):
                lo.append(int(v))
            if isinstance(v := st.attributes.get("max_color_temp_kelvin"), (int, float)):
                hi.append(int(v))
    supported: set[ColorMode] = set()
    if modes & RGB_COLOR_MODES:
        supported.add(ColorMode.HS)
    if modes & KELVIN_COLOR_MODES:
        supported.add(ColorMode.COLOR_TEMP)
    if not supported:
        supported = {ColorMode.BRIGHTNESS}
    mode = ColorMode.BRIGHTNESS if supported == {ColorMode.BRIGHTNESS} else None
    hs = kelvin = None
    for e in lamps:
        st = hass.states.get(e)
        if st is None or st.state != STATE_ON:
            continue
        if ColorMode.HS in supported and str(st.attributes.get("color_mode")) in RGB_COLOR_MODES and st.attributes.get("hs_color"):
            mode, hs = ColorMode.HS, tuple(st.attributes["hs_color"])
            break
        if ColorMode.COLOR_TEMP in supported and isinstance(st.attributes.get("color_temp_kelvin"), (int, float)):
            mode, kelvin = ColorMode.COLOR_TEMP, int(st.attributes["color_temp_kelvin"])
            break
    if mode is None:
        mode = ColorMode.COLOR_TEMP if ColorMode.COLOR_TEMP in supported else next(iter(supported))
    return {
        "supported": supported, "mode": mode, "hs": hs, "kelvin": kelvin,
        "min_kelvin": min(lo) if lo else 2000, "max_kelvin": max(hi) if hi else 6500,
    }


def _colour_request(kwargs: dict[str, Any]) -> dict[str, Any]:
    """The colour part of a turn_on call on a RoomControl light."""
    return {k: kwargs[k] for k in (ATTR_HS_COLOR, ATTR_COLOR_TEMP_KELVIN) if k in kwargs}


def _unique_id(area_id: str) -> str:
    return f"{DOMAIN}_{area_id}"


@callback
def _rename_room_entity_ids(hass: HomeAssistant, entry_id: str, device_id: str, old: str, new: str) -> None:
    """A room was renamed: entity IDs made from its old name
    (<domain>.roomcontrol_<old>…) get the new name; an ID the user chose
    (not starting with roomcontrol_<old>) is left alone."""
    old_slug, new_slug = slugify(old), slugify(new)
    if not old_slug or not new_slug or old_slug == new_slug:
        return
    ent_reg = er.async_get(hass)
    prefix = f"{DOMAIN}_{old_slug}"
    for ent in list(er.async_entries_for_device(ent_reg, device_id, include_disabled_entities=True)):
        if ent.config_entry_id != entry_id:
            continue
        domain, object_id = ent.entity_id.split(".", 1)
        if object_id != prefix and not object_id.startswith(f"{prefix}_"):
            continue
        wanted = f"{domain}.{DOMAIN}_{new_slug}{object_id[len(prefix):]}"
        if ent_reg.async_get(wanted) is not None or hass.states.get(wanted) is not None:
            continue  # taken: leave this one
        _LOGGER.info("Room renamed: %s → %s", ent.entity_id, wanted)
        ent_reg.async_update_entity(ent.entity_id, new_entity_id=wanted)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities = with_roomcontrol_ids(hass, "light", async_add_entities)
    """Create a room light (and device) for every managed room, keep that in
    sync, and remove the devices of areas RoomControl does not manage."""
    area_reg = ar.async_get(hass)
    known: dict[str, RoomControlLight] = {}

    @callback
    def _sync_rooms(*_: Any) -> None:
        wanted = managed_areas(hass)
        new = [RoomControlLight(hass, a) for a in wanted - known.keys()]
        for entity in new:
            known[entity._area_id] = entity
        if new:
            async_add_entities(new)
        ent_reg = er.async_get(hass)
        for area_id in list(known.keys() - wanted):
            del known[area_id]
            if entity_id := ent_reg.async_get_entity_id("light", DOMAIN, _unique_id(area_id)):
                ent_reg.async_remove(entity_id)
        # Devices of unmanaged areas (also those left from older versions,
        # which gave every area a device) leave the integration page.
        # Sub-devices of an older version ("<area>::wekkers" …) go once their
        # entities are back on the room's device; the General device stays.
        dev_reg = dr.async_get(hass)
        for device in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
            ids = [i[1] for i in device.identifiers if i[0] == DOMAIN]
            if not ids or GENERAL_DEVICE in ids:
                continue
            parts = [split_identifier(i) for i in ids]
            area_ids = {a for a, _ in parts}
            is_sub = any(kind for _, kind in parts)
            gone = not area_ids & wanted
            empty = is_sub and not er.async_entries_for_device(ent_reg, device.id)
            if gone or empty:
                dev_reg.async_update_device(device.id, remove_config_entry_id=entry.entry_id)

    _sync_rooms()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_rooms))

    @callback
    def _on_area_event(event: Event) -> None:
        action = event.data.get("action")
        area_id = event.data.get("area_id")
        if not area_id:
            return
        if action in ("create", "remove"):
            _sync_rooms()
        elif action == "update":
            # The area was renamed: the room's device, its entity IDs and every
            # name RoomControl shows follow right away.
            dev_reg = dr.async_get(hass)
            device = dev_reg.async_get_device(identifiers={(DOMAIN, area_id)})
            area = area_reg.async_get_area(area_id)
            if area and device and device.name != area.name:
                old = device.name or ""
                dev_reg.async_update_device(device.id, name=area.name)
                _rename_room_entity_ids(hass, entry.entry_id, device.id, old, area.name)
            async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED)

    entry.async_on_unload(hass.bus.async_listen(ar.EVENT_AREA_REGISTRY_UPDATED, _on_area_event))

    # Lamp groups from the panel: one light entity per group, on the room's device.
    group_entities: dict[tuple[str, str], LampGroupLight] = {}

    @callback
    def _sync_groups(*_: Any) -> None:
        rooms = hass.data.get(DOMAIN, {}).get("rooms", [])
        wanted = {
            (room["area_id"], group["id"])
            for room in rooms
            if room.get("area_id") in known
            for group in room.get(CONF_GROUPS, []) or []
            if group.get("id")
        }
        new = [LampGroupLight(hass, a, g) for (a, g) in wanted - group_entities.keys()]
        ent_reg = er.async_get(hass)
        for entity in new:
            group_entities[(entity.area_id, entity.group_id)] = entity
            _group_entity_id(hass, ent_reg, entity)
        if new:
            async_add_entities(new)
        for key in list(group_entities.keys() - wanted):
            del group_entities[key]
            if entity_id := ent_reg.async_get_entity_id("light", DOMAIN, _group_unique_id(*key)):
                ent_reg.async_remove(entity_id)

    _sync_groups()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _sync_groups))


def _group_unique_id(area_id: str, group_id: str) -> str:
    return f"{DOMAIN}_{area_id}_group_{group_id}"


def _group_object_id(hass: HomeAssistant, area_id: str, name: str) -> str:
    """light.roomcontrol_<room>_<bundle>, e.g. roomcontrol_tuin_bundel_1 for
    "Lichtbundel 1" or "Tuin lichtbundel 1" in the area Tuin (the room only once)."""
    area = ar.async_get(hass).async_get_area(area_id)
    room = slugify(area.name if area else area_id)
    bundle = slugify(name)
    if bundle != room and not bundle.startswith(f"{room}_"):
        bundle = f"{room}_{bundle}" if bundle else room
    return f"{DOMAIN}_{bundle}"


@callback
def _group_entity_id(hass: HomeAssistant, ent_reg: er.EntityRegistry, entity: LampGroupLight) -> None:
    """Give a bundle light the entity ID light.roomcontrol_<room>_<bundle>.

    New bundles get it at registration. Bundles registered before, with the ID
    Home Assistant made itself (<device>_<name>, e.g. light.tuin_tuin_bundel_1),
    are renamed once; an ID the user chose is left alone."""
    name = entity.group_id
    for index, group in enumerate((stored_room(hass, entity.area_id) or {}).get(CONF_GROUPS, []) or []):
        if group.get("id") == entity.group_id:
            name = (group.get("name") or "").strip() or f"Groep {index + 1}"
            break
    object_id = _group_object_id(hass, entity.area_id, name)
    wanted = f"light.{object_id}"
    # Suggested ID: used for a new bundle, and stored in the registry so Home
    # Assistant's "recreate entity ID" gives this ID too.
    entity.entity_id = wanted
    current = ent_reg.async_get_entity_id("light", DOMAIN, entity.unique_id)
    if current is None:
        return
    if current == wanted or current.startswith(f"light.{DOMAIN}_"):
        return
    entry = ent_reg.async_get(current)
    device = dr.async_get(hass).async_get(entry.device_id) if entry and entry.device_id else None
    device_name = (device.name_by_user or device.name) if device else ""
    auto = slugify(f"{device_name} {entry.original_name or name}" if entry else "")
    current_obj = current.split(".", 1)[1]
    made_by_ha = bool(auto) and (current_obj == auto or (
        current_obj.startswith(f"{auto}_") and current_obj[len(auto) + 1:].isdigit()
    ))
    if not made_by_ha or ent_reg.async_is_registered(wanted) or hass.states.get(wanted) is not None:
        return
    _LOGGER.info("Renaming %s to %s", current, wanted)
    ent_reg.async_update_entity(current, new_entity_id=wanted)


class LampGroupLight(LightEntity):
    """A lamp group from the panel, as a light on the room's device.

    Switching and dimming go through the room light, so fixed levels, the
    daylight colour and the room's rules (time slots, presence, manual control)
    apply exactly as for the room itself.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_icon = "mdi:lightbulb-group-outline"

    def __init__(self, hass: HomeAssistant, area_id: str, group_id: str) -> None:
        self.area_id = area_id
        self.group_id = group_id
        self._attr_unique_id = _group_unique_id(area_id, group_id)
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, area_id)})
        self._lamps: list[str] = []
        self._unsub: CALLBACK_TYPE | None = None

    def _group(self) -> tuple[int, dict[str, Any]] | None:
        room = stored_room(self.hass, self.area_id) or {}
        for index, group in enumerate(room.get(CONF_GROUPS, []) or []):
            if group.get("id") == self.group_id:
                return index, group
        return None

    @property
    def name(self) -> str:
        found = self._group()
        if not found:
            return self.group_id
        index, group = found
        # Same name as in the panel; an empty name shows as "Groep n" there too.
        return (group.get("name") or "").strip() or f"Groep {index + 1}"

    @callback
    def _refresh(self, *_: Any) -> None:
        found = self._group()
        room_lamps = room_lights(self.hass, self.area_id)
        lamps = [e for e in (found[1].get("lights", []) if found else []) if e in room_lamps]
        if lamps != self._lamps:
            if self._unsub:
                self._unsub()
            self._lamps = lamps
            self._unsub = async_track_state_change_event(self.hass, lamps, self._refresh) if lamps else None
        states = [self.hass.states.get(e) for e in self._lamps]
        on = [st for st in states if st is not None and st.state == STATE_ON]
        brightness = [
            st.attributes[ATTR_BRIGHTNESS] for st in on
            if isinstance(st.attributes.get(ATTR_BRIGHTNESS), (int, float))
        ]
        self._attr_available = any(st is not None for st in states)
        self._attr_is_on = bool(on)
        self._attr_brightness = round(sum(brightness) / len(brightness)) if brightness else None
        colour = _colour_state(self.hass, self._lamps)
        self._attr_supported_color_modes = colour["supported"]
        self._attr_color_mode = colour["mode"]
        self._attr_hs_color = colour["hs"]
        self._attr_color_temp_kelvin = colour["kelvin"]
        self._attr_min_color_temp_kelvin = colour["min_kelvin"]
        self._attr_max_color_temp_kelvin = colour["max_kelvin"]
        self._attr_extra_state_attributes = {
            ATTR_ENTITY_ID: list(self._lamps),
            "roomcontrol_area": self.area_id,
            "roomcontrol_group": self.group_id,
        }
        if self.entity_id:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._refresh()
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._refresh))

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _room_light(self) -> RoomControlLight | None:
        return self.hass.data.get(DOMAIN, {}).get("entities", {}).get(self.area_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        room = self._room_light()
        if room is None:
            return
        lamps = room.lamps_allowed(self._lamps)
        if self._lamps and not lamps:
            raise HomeAssistantError(f"{self.name}: lights are blocked (nobody home)")
        data = {ATTR_BRIGHTNESS: kwargs[ATTR_BRIGHTNESS]} if ATTR_BRIGHTNESS in kwargs else {}
        await room.async_call_lamps("turn_on", lamps, **data, **_colour_request(kwargs))

    async def async_turn_off(self, **kwargs: Any) -> None:
        room = self._room_light()
        if room is not None:
            await room.async_call_lamps("turn_off", self._lamps)


class RoomControlLight(LightEntity):
    """Controls all lights of one room (area) as a single entity."""

    @property
    def name(self) -> str | None:
        """The name given to the room's lamp group, or None (= the room's name)."""
        if self.hass is None:
            return None
        return (self._room.get(CONF_LIGHTS_NAME) or "").strip() or None

    _attr_has_entity_name = True
    _attr_name = None  # use the device (area) name
    _attr_should_poll = False
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_icon = "mdi:lightbulb-group"

    def __init__(self, hass: HomeAssistant, area_id: str) -> None:
        self._area_id = area_id
        area = ar.async_get(hass).async_get_area(area_id)
        name = area.name if area else area_id

        self._attr_unique_id = _unique_id(area_id)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, area_id)},
            name=name,
            manufacturer="RoomControl",
            sw_version=VERSION,
            suggested_area=name,
        )
        self._members: list[str] = []
        # key -> (tracked entity ids, unsubscribe)
        self._tracks: dict[str, tuple[tuple[str, ...], CALLBACK_TYPE]] = {}
        self._allowed: bool | None = None
        # Curtains that follow dark/light: last wanted state (True = open)
        self._covers_open: bool | None = None
        self._covers_init = False
        self._cancel_cover_time: CALLBACK_TYPE | None = None
        # Lux control: periodic check and when we last adjusted
        self._cancel_lux_interval: CALLBACK_TYPE | None = None
        # Time slot running + sun down: check every minute that the bundles are on.
        self._cancel_evening_check: CALLBACK_TYPE | None = None
        self._evening_last_fix: datetime | None = None
        self._lux_last_adjust: datetime | None = None
        # Fan: the activity is shared by all rooms using the same fans (see
        # fan_activity.py); this is the key of the fans this room last drove.
        self._fan_key: FanKey | None = None
        # Fan by temperature: speed wanted now (None = temperature not in range)
        self._fan_temp_pct: int | None = None
        # Last non-transitional alarm state, so disarmed → arming → armed_home counts.
        self._alarm_settled: str | None = None
        # When the alarm last switched the room's lights off (for the panel)
        self._alarm_last_off: datetime | None = None
        # 1% mode switched on by the alarm (so leaving armed home restores it)
        self._dim_by_alarm = False
        self._alarm_started = False
        # Grace period end from before a restart (used once by _check_idle)
        self._restored_grace: datetime | None = None
        # Lamps of bundles with own times whose slot was running (None: not checked yet)
        self._own_prev: set[str] | None = None
        # Lamps in Dim because their time slot's Dim time has come
        self._dim_slots: set[str] = set()
        self._dim_option_seen: tuple[bool, ...] | None = None
        # (sun phase, someone home) at the last evaluation
        self._conditions: tuple[str, bool] | None = None
        # Debug log: why bundles did or did not go on/off (newest last).
        self._debug: deque[dict[str, Any]] = deque(maxlen=80)
        # "Later thuis": an off was held back; do it once the person is home.
        self._late_pending = False
        # "Later thuis": the bundles were switched on for it already.
        self._late_on_done = False
        self._on_by_motion = False
        # Lamps whose bundle reacted to motion at the last config (None: not read yet)
        self._prev_motion_lamps: set[str] | None = None
        self._prev_dim_lamps: set[str] | None = None
        self._cancel_motion_off: CALLBACK_TYPE | None = None
        # End of the running grace period (no motion, lights still on), UTC
        self._grace_until: datetime | None = None
        # Why the last motion did not switch the lights on (None = it did)
        self._motion_note: str | None = None
        # Manual control: RoomControl does nothing automatic until this time (UTC)
        self._manual_until: datetime | None = None
        self._cancel_manual: CALLBACK_TYPE | None = None
        self._cancel_daylight: CALLBACK_TYPE | None = None
        self._last_kelvins: dict[str, int] = {}
        # 1% dim: brightness per lamp before dimming (None = was off)
        # 1% mode, per lamp. Sources: the room button / alarm (all lamps) and
        # time slots with a Dim time. Remembered brightness per dimmed lamp,
        # restored when no source dims it any more.
        self._dim_room = False
        # Lamps of alarm clocks going off at the last check (Dim paused for them)
        self._clock_prev: set[str] = set()
        self._dim_saved: dict[str, int] = {}
        # Smart options. Last no-motion off (adaptive grace period).
        self._idle_off_at: datetime | None = None
        # Re-check when the "last motion was here" hold ends.
        self._cancel_hold: CALLBACK_TYPE | None = None
        # Lux model: lux per brightness step (0-255), and what we measured at the last adjustment.
        self._lux_gain: float | None = None
        self._lux_probe: tuple[float, float, tuple[str, ...]] | None = None
        # Lamps lux control already asked for the lowest level (too light):
        # still too light next time → off (some lamps can't go that low).
        self._lux_min_asked: tuple[str, ...] | None = None
        # Brightness set by hand, waiting to settle before it is learned.
        self._bright_pending: dict[str, CALLBACK_TYPE] = {}
        # When the room's lamps went on (sessions for replay) and which lamps were on.
        self._session_start: datetime | None = None
        self._session_lamps: set[str] = set()
        self._session_skip = False
        # Lamps the replay switched on.
        self._replay_on: set[str] = set()
        self._cancel_smart_tick: CALLBACK_TYPE | None = None
        self._last_motion_at: datetime = dt_util.utcnow()
        self._anomaly_sent: dict[str, datetime] = {}
        self._long_on_sent = False
        # Lamps whose brightness a person changed: RoomControl leaves their
        # brightness alone (lux control, schemer) until they go off.
        self._hand_set: set[str] = set()

    # ── config & subscriptions ─────────────────────────────────────────────

    @property
    def _room(self) -> dict[str, Any]:
        return stored_room(self.hass, self._area_id) or {}

    @callback
    def _track(
        self, key: str, entity_ids: list[str], handler: Callable[[Event], None]
    ) -> bool:
        """Track state changes of `entity_ids` under `key`; True if it changed."""
        ids = tuple(e for e in entity_ids if e)
        current = self._tracks.get(key)
        if current and current[0] == ids:
            return False
        if current:
            current[1]()
            del self._tracks[key]
        if ids:
            self._tracks[key] = (
                ids,
                async_track_state_change_event(self.hass, list(ids), handler),
            )
        return True

    @callback
    def _subscribe(self) -> None:
        """(Re)subscribe after a config or area change, then re-evaluate."""
        room = self._room
        self._members = room_lights(self.hass, self._area_id)
        self._track("members", self._members, self._on_member_change)

        alarm = self._alarm_entity() if self._members else None
        if self._track("alarm", [alarm] if alarm else [], self._on_alarm_change):
            self._alarm_settled = self._settled(self.hass.states.get(alarm)) if alarm else None
        # Dim at armed home: apply at startup and when the option is switched.
        dim_wanted = (bool(alarm), room.get(CONF_ARMED_HOME_MODE) == ARMED_HOME_NO_MOTION)
        if dim_wanted != self._dim_option_seen:
            self._dim_option_seen = dim_wanted
            self._reconcile_alarm_dim()

        self._track("presence", room_persons(self.hass, room), self._on_presence_change)
        self._track("motion", self._motion_sensors(), self._on_motion_change)
        self._track("media", self._media_players() if room.get(CONF_MEDIA_HOLD) else [], self._on_media_change)
        self._setup_smart_tick()
        self._track("door", [s for s in room.get(CONF_DOOR_SENSORS, []) or [] if s], self._on_door_change)
        self._track("locks", [lock["entity_id"] for lock in room_locks(room)], self._on_lock_change)
        self._track("sun", [self._sun_entity()] if self._members or self._following_covers() else [], self._on_sun_change)
        self._setup_daylight()
        self._setup_lux_control()
        self._setup_evening_check()
        self._setup_fan_temp()
        # Fans, steps or activity control changed in the panel: re-evaluate.
        self._fan_update(write=False)
        self._recompute()
        # A config change (or startup) only remembers what the curtains should
        # be; they move at the next real change of daylight or opening time.
        self._covers_init = False
        self._setup_cover_time()
        self._evaluate_covers()
        self._evaluate_conditions()

    # ── follow daylight ────────────────────────────────────────────────────

    # ── bundles: per-lamp settings ─────────────────────────────────────────
    #
    # Lamps are configured in bundles (the room's lamp groups; one bundle per
    # lamp). A bundle may set: brightness_mode ("default"/"fixed") + brightness,
    # follow_daylight, daylight_prefer_rgb, daylight_min/max_kelvin, on_motion,
    # on_door, on_dusk, follow_schedule, dim, lux_control. A setting a bundle
    # does not have falls back to the room's own setting (older rooms).

    def _bundle(self, lamp: str) -> dict[str, Any] | None:
        for group in self._room.get(CONF_GROUPS, []) or []:
            if lamp in (group.get("lights") or []):
                return group
        return None

    def _bopt(self, lamp: str, key: str, fallback: Any) -> Any:
        bundle = self._bundle(lamp)
        return bundle[key] if bundle is not None and key in bundle else fallback

    def _lamps_where(self, key: str, fallback: Any) -> list[str]:
        """Room lamps whose bundle (or the room) has `key` switched on."""
        return [e for e in self._members if self._bopt(e, key, fallback)]

    def _motion_lamps(self) -> list[str]:
        """Lamps that go on with motion (bundle "on_motion", default yes)."""
        return self._lamps_where("on_motion", True)

    # ── own times per bundle ───────────────────────────────────────────────
    # A bundle with "own_times" has its own time slots: [{"days": [0..6] (Monday = 0), "start": {"type": "time",
    # "time": "HH:MM"} | {"type": "dusk"} | {"type": "dark"}, "end": {"type":
    # "time", "time": "HH:MM"} | {"type": "sunrise"}, "dim_at": "HH:MM" (optional:
    # Dim from then until the end)}]. A slot that ends
    # before it starts (or at sunrise) runs past midnight into the next day.

    def _own_lamps(self) -> list[str]:
        return [e for e in self._members if self._bopt(e, "own_times", False)]

    @staticmethod
    def _hm(value: Any) -> int | None:
        return hm_minutes(value)

    def _slot_active(self, slot: dict[str, Any], now: datetime, phase: str) -> bool:
        return self._slot_part(slot, now, phase) is not None

    def _slot_part(self, slot: dict[str, Any], now: datetime, phase: str) -> str | None:
        """"today" (the slot started today), "carry" (yesterday's slot running
        past midnight) or None (not running)."""
        return slot_part(slot, now, phase, self._sun_down())

    def _slot_dim_now(self, slot: dict[str, Any], now: datetime, phase: str) -> bool:
        """The slot runs and its Dim time ("dim_at") has come: Dim until it ends."""
        dim = self._hm(slot.get("dim_at"))
        part = self._slot_part(slot, now, phase) if dim is not None else None
        if part is None:
            return False
        start = slot.get("start") or {}
        s_ref = (self._hm(start.get("time")) or 0) if start.get("type", "time") == "time" else 12 * 60
        t = now.hour * 60 + now.minute
        if part == "today":
            return dim >= s_ref and t >= dim  # a Dim time before the start is after midnight
        return dim >= s_ref or t >= dim

    def _slot_dim_lamps(self) -> set[str]:
        """Lamps whose running time slot is past its Dim time."""
        now, phase = dt_util.as_local(dt_util.now()), self._phase()
        return {
            e for e in self._own_lamps()
            if any(self._slot_dim_now(s, now, phase) for s in self._mode_slots(e))
        }

    @callback
    def _update_slot_dim(self) -> None:
        """Lamps reach / leave their slot's Dim time: to Dim, or back."""
        if self._manual:
            return
        wanted = self._slot_dim_lamps()
        if wanted == self._dim_slots:
            return
        before = self._dimmed_lamps()
        self._dim_slots = wanted
        after = self._dimmed_lamps()
        self.hass.async_create_task(self._async_apply_dim(before, after))

    def _dim_pct(self, lamp: str) -> int:
        """Dim level of a lamp (Dim button, alarm, time slot): the general
        setting (default 1%)."""
        value = self._settings().get(SETTING_DIM_LEVEL, DIM_LEVEL_DEFAULT)
        return int(min(100, max(1, value))) if isinstance(value, (int, float)) and value > 0 else DIM_LEVEL_DEFAULT

    def _own_slot_now(self, lamp: str) -> dict[str, Any] | None:
        """The slot of this lamp's bundle that is running now (None: none)."""
        if not self._bopt(lamp, "own_times", False):
            return None
        now, phase = dt_util.as_local(dt_util.now()), self._phase()
        for slot in self._mode_slots(lamp):
            if self._slot_active(slot, now, phase):
                return slot
        return None

    def _mode_slots(self, lamp: str) -> list[dict[str, Any]]:
        """The slots that count now: normal ones; during vacation (the
        "Vakantie" switch) the bundle's vacation slots — or, when it has none,
        its normal slots."""
        from .slots import mode_slots  # noqa: PLC0415

        return mode_slots(self._bopt(lamp, "slots", []) or [], self.hass.data.get(DOMAIN, {}).get("vacation"))

    def _own_active(self) -> list[str]:
        """Lamps of bundles with own times whose slot is running now."""
        return [e for e in self._own_lamps() if self._own_slot_now(e) is not None]

    def _dusk_bundle(self, lamp: str) -> bool:
        """A running own slot that starts at schemer (it gets the schemer level /
        lux control)."""
        slot = self._own_slot_now(lamp)
        return slot is not None and (slot.get("start") or {}).get("type") == "dusk"

    @callback
    def _evaluate_own_times(self) -> bool:
        """Slots start or end: their lamps go on (at their level) or off
        (unless someone is moving and motion may keep them on)."""
        active = set(self._own_active())
        # First check (startup / config loaded): the lamps take the state their slots ask for right away.
        previous, self._own_prev = (self._own_prev or set()), active
        if self._manual or self._alarm_mode() == "home":
            return False
        if not presence_allows(self.hass, self._room):
            return False
        acted = False
        blocked = self._alarm_blocked()
        lux = set(self._lux_lamps_now())
        started = [e for e in active - previous if e not in blocked and e not in lux]
        if started:
            self._on_by_motion = False
            self._auto_on("own times", lamps=started, levels=self._phase_levels(started))
            acted = True
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
        ended = [e for e in previous - active if is_on(e)]
        if ended:
            if self._any_motion() and (self._sun_down() or self._is_dark()):
                self._on_by_motion = True
            else:
                self._auto_off("own times ended", lamps=ended)
                acted = True
        if active & lux:
            self._regulate_lux(force=True)
        return acted

    def lamps_allowed(self, lamps: list[str]) -> list[str]:
        """Of `lamps`, those that may be switched on now (by hand or automatically):
        all of them when someone is home; during manual control always."""
        if self._manual:
            return list(lamps)
        if not presence_allows(self.hass, self._room):
            return []
        return list(lamps)

    def _follows_daylight(self) -> bool:
        return bool(self._daylight_lamps())

    def _daylight_lamps(self) -> list[str]:
        """Lamps that follow the sun (bundle setting, else the room's choice)."""
        room = self._room
        chosen = room.get(CONF_DAYLIGHT_LIGHTS)
        room_on = bool(room.get(CONF_FOLLOW_DAYLIGHT))
        return [
            e for e in self._members
            if self._bopt(e, "follow_daylight", room_on and (chosen is None or e in chosen))
        ]

    def _kelvin_for(self, lamp: str) -> int | None:
        if self._manual or lamp not in self._daylight_lamps():
            return None
        room = self._room
        lo = self._bopt(lamp, "daylight_min_kelvin", room.get(CONF_DAYLIGHT_MIN_KELVIN)) or DAYLIGHT_MIN_KELVIN
        hi = self._bopt(lamp, "daylight_max_kelvin", room.get(CONF_DAYLIGHT_MAX_KELVIN)) or DAYLIGHT_MAX_KELVIN
        lo, hi = int(min(lo, hi)), int(max(lo, hi))
        return daylight_kelvin(self.hass, self._sun_entity(), lo, hi)

    def _kelvin(self) -> int | None:
        """The room's daylight colour (first lamp that follows the sun), for display."""
        lamps = self._daylight_lamps()
        return self._kelvin_for(lamps[0]) if lamps else None

    def _colour_data(self, entity_id: str, kelvin: int) -> dict[str, Any]:
        """Colour for one lamp (after Adaptive Lighting).

        Colour lamps with "prefer RGB" (or without colour temperature) get the
        sun's colour as rgb_color; other lamps get color_temp_kelvin, kept
        within the lamp's own supported range.
        """
        state = self.hass.states.get(entity_id)
        modes = {str(m) for m in (state.attributes.get("supported_color_modes") or [])} if state else set()
        rgb_capable = bool(modes & RGB_COLOR_MODES)
        ct_capable = "color_temp" in modes
        prefer_rgb = self._bopt(entity_id, "daylight_prefer_rgb", self._room.get(CONF_DAYLIGHT_PREFER_RGB))
        if rgb_capable and (prefer_rgb or not ct_capable):
            r, g, b = color_temperature_to_rgb(kelvin)
            return {"rgb_color": (int(round(r)), int(round(g)), int(round(b)))}
        lo = state.attributes.get("min_color_temp_kelvin") if state else None
        hi = state.attributes.get("max_color_temp_kelvin") if state else None
        if isinstance(lo, (int, float)):
            kelvin = max(kelvin, int(lo))
        if isinstance(hi, (int, float)):
            kelvin = min(kelvin, int(hi))
        return {"color_temp_kelvin": kelvin}

    def _daylight_members(self) -> list[str]:
        """Lamps that follow the sun and can take a colour temperature."""
        return [e for e in self._daylight_lamps() if supports_kelvin(self.hass, e)]

    @callback
    def _setup_daylight(self) -> None:
        if self._follows_daylight() and self._cancel_daylight is None:
            self._cancel_daylight = async_track_time_interval(
                self.hass, self._daylight_tick, timedelta(seconds=DAYLIGHT_UPDATE_INTERVAL)
            )
        elif not self._follows_daylight() and self._cancel_daylight is not None:
            self._cancel_daylight()
            self._cancel_daylight = None
            self._last_kelvins = {}

    @callback
    def _daylight_tick(self, _now: Any = None) -> None:
        """Shift lights that are on towards the current daylight colour."""
        wanted = {
            e: k for e in self._daylight_members()
            if (s := self.hass.states.get(e)) is not None and s.state == STATE_ON
            and (k := self._kelvin_for(e)) is not None
        }
        changed = {e: k for e, k in wanted.items() if self._last_kelvins.get(e) != k}
        self._last_kelvins = {e: k for e, k in wanted.items()}
        if changed:
            self.hass.async_create_task(self._async_set_kelvins(changed))

    def _fixed_levels(self) -> dict[str, int]:
        """Lamps at a fixed level: {entity_id: percent 1-100} (bundle, else room pin)."""
        room_levels = self._room.get(CONF_FIXED_LEVELS) or {}
        out: dict[str, int] = {}
        for e in self._members:
            bundle = self._bundle(e)
            if bundle is not None and "brightness_mode" in bundle:
                value = bundle.get("brightness") if bundle.get("brightness_mode") == "fixed" else None
            else:
                value = room_levels.get(e)
            if isinstance(value, (int, float)) and value > 0:
                out[e] = int(min(100, max(1, value)))
        return out

    def _default_pct_for(self, lamp: str) -> int | None:
        """Standard brightness for a lamp: learned for this hour (never above
        the bundle's maximum), else the bundle's level."""
        top = self._auto_max_pct(lamp)
        if self._room.get(CONF_LEARN_BRIGHTNESS) and (learn := self._learn()) is not None:
            learned = learn.learned_pct(self._area_id, lamp, dt_util.now().hour)
            if learned is not None:
                return min(learned, top) if top else learned
        return top

    def _auto_max_pct(self, lamp: str) -> int | None:
        """The bundle's level (panel slider): what RoomControl switches it on
        at, and the most it makes it by itself (motion, times, lux control).
        A person may set it brighter by hand. None: the lamp's own level."""
        bundle = self._bundle(lamp)
        if bundle is not None and "brightness_mode" in bundle:
            value = bundle.get("brightness") if bundle.get("brightness_mode") == "default" else None
        else:
            value = self._room.get(CONF_DEFAULT_BRIGHTNESS)
        if not isinstance(value, (int, float)) or value <= 0:
            return None
        return int(min(100, max(1, value)))

    async def _async_adjust(self, entity_id: str, kelvin: int | None, pct: int | None) -> None:
        data: dict[str, Any] = {ATTR_ENTITY_ID: [entity_id]}
        if kelvin is not None:
            data.update(self._colour_data(entity_id, kelvin))
        if pct is not None:
            data["brightness_pct"] = pct
        await rc_call(self.hass,"light", "turn_on", data, blocking=True)

    async def _async_set_kelvins(self, kelvins: dict[str, int]) -> None:
        # Lamps that get the same colour data share one call.
        groups: dict[tuple[tuple[str, Any], ...], list[str]] = {}
        for entity_id, kelvin in kelvins.items():
            groups.setdefault(tuple(sorted(self._colour_data(entity_id, kelvin).items())), []).append(entity_id)
        for colour, ids in groups.items():
            await rc_call(self.hass,
                "light", "turn_on", {ATTR_ENTITY_ID: ids, **dict(colour), "transition": 2}, blocking=True
            )

    @callback
    def _recompute(self) -> None:
        states = [self.hass.states.get(e) for e in self._members]
        on = [s for s in states if s is not None and s.state == STATE_ON]
        self._attr_available = any(s is not None for s in states)
        self._attr_is_on = bool(on)
        brightnesses = [
            s.attributes[ATTR_BRIGHTNESS]
            for s in on
            if isinstance(s.attributes.get(ATTR_BRIGHTNESS), (int, float))
        ]
        self._attr_brightness = (
            round(sum(brightnesses) / len(brightnesses)) if brightnesses else None
        )
        colour = _colour_state(self.hass, self._members)
        self._attr_supported_color_modes = colour["supported"]
        self._attr_color_mode = colour["mode"]
        self._attr_hs_color = colour["hs"]
        self._attr_color_temp_kelvin = colour["kelvin"]
        self._attr_min_color_temp_kelvin = colour["min_kelvin"]
        self._attr_max_color_temp_kelvin = colour["max_kelvin"]
        self._attr_extra_state_attributes = {
            ATTR_ENTITY_ID: list(self._members),
            "presence_allows": presence_allows(self.hass, self._room),
            "daylight_kelvin": self._kelvin(),
            "dimmed": self._dim_room,
            "follows_dim": self.follows_dim,
            "neighbours": room_neighbours(self.hass, self._area_id),
            "dimmed_lamps": sorted(self._dimmed_lamps()),
            "roomcontrol_area": self._area_id,
            "alarm_last_off": self._alarm_last_off.isoformat() if self._alarm_last_off else None,
            "armed_home_motion_only": self._armed_home_motion_only(),
            "armed_home_no_motion": self._armed_home_no_motion(),
            **self._vacuum_attrs(),
            **self._fan_activity_attrs(),
            "fan_temp_active": self._fan_temp_pct is not None,
            "fan_nobody_home": bool(self._fans()) and not anyone_home(self.hass),
            "fixed_levels": self._fixed_levels(),
            "motion_sensors": self._motion_sensors(),
            "motion_note": self._motion_note,
            "manual_until": self._manual_until.isoformat() if self._manual_until else None,
            "manual_duration": self._manual_duration(),
            "motion_off_delay": self._motion_off_delay(),
            "grace_until": self._grace_until.isoformat() if self._grace_until else None,
            "linked_rooms": [a for a in linked_group(self.hass, self._area_id) if a != self._area_id],
            "smart": self._smart_attrs(),
            "hand_set": sorted(self._hand_set),
            **self._clock_attrs(),
            "smoke": manager.status() if (manager := self.hass.data.get(DOMAIN, {}).get("smoke")) else None,
        }

    @callback
    def _on_member_change(self, event: Event) -> None:
        # A lamp switched on by anyone gets the daylight colour right away.
        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        if smoke_active(self.hass):
            # Smoke: lamps stay as they are (full on), no Dim, level or colour.
            self._recompute()
            self.async_write_ha_state()
            return
        if (
            new is not None and new.state == STATE_ON
            and isinstance(b := new.attributes.get(ATTR_BRIGHTNESS), (int, float)) and b <= ZERO_BRIGHTNESS
        ):
            # On at 0% (dimmed all the way down, by anyone): switch it off.
            self._dbg("off", "zero_pct", [new.entity_id])
            self.hass.async_create_task(
                rc_call(self.hass, "light", "turn_off", {ATTR_ENTITY_ID: [new.entity_id]}, blocking=True)
            )
            return
        # A lamp switched on by anyone gets its fixed level and daylight colour.
        if new is not None and new.state == STATE_ON and (old is None or old.state != STATE_ON) and self._lamp_dimmed(new.entity_id):
            # 1% mode: a lamp switched on (by anyone) burns at 1%. Remember the
            # brightness it came on with, unless we switched it on ourselves.
            brightness = new.attributes.get(ATTR_BRIGHTNESS)
            if not isinstance(brightness, (int, float)) or brightness / 255 * 100 > 1.5:
                if new.entity_id not in self._dim_saved:
                    self._dim_remember(new.entity_id, brightness if isinstance(brightness, (int, float)) else 255)
                kelvin = self._kelvin_for(new.entity_id) if new.entity_id in self._daylight_members() else None
                self.hass.async_create_task(self._async_adjust(new.entity_id, kelvin, 1))
        elif new is not None and new.state == STATE_ON and (old is None or old.state != STATE_ON):
            kelvin = self._kelvin_for(new.entity_id) if new.entity_id in self._daylight_members() else None
            if kelvin is not None:
                wanted = self._colour_data(new.entity_id, kelvin)
                if all(
                    tuple(new.attributes.get(k)) == tuple(v) if isinstance(v, tuple) else new.attributes.get(k) == v
                    for k, v in wanted.items()
                    if new.attributes.get(k) is not None
                ) and any(new.attributes.get(k) is not None for k in wanted):
                    kelvin = None  # already in the daylight colour
            if not self._recently_commanded(new.entity_id):
                self._dbg("info", "external_on", [new.entity_id])
            pct = self._fixed_levels().get(new.entity_id)
            if pct is None and not self._recently_commanded(new.entity_id):
                # Switched on by someone else (wall switch, app, automation): the
                # bundle's standard level, like RoomControl would have used.
                pct = self._default_pct_for(new.entity_id)
            brightness = new.attributes.get(ATTR_BRIGHTNESS)
            if pct is not None and isinstance(brightness, (int, float)) and abs(brightness / 255 * 100 - pct) <= 1.5:
                pct = None  # already at its level
            if kelvin is not None or pct is not None:
                self.hass.async_create_task(self._async_adjust(new.entity_id, kelvin, pct))
        if (
            new is not None and new.state != STATE_ON and old is not None and old.state == STATE_ON
            and new.entity_id in self._evening_lamps() and self._keep_evening_on("time slot, sun down: back on")
        ):
            pass  # time slot running + sun down: this bundle stays on
        if new is not None and new.state != STATE_ON:
            self._hand_set.discard(new.entity_id)  # off: RoomControl may set it again next time
        if (
            new is not None and old is not None and new.state == STATE_ON and old.state == STATE_ON
            and isinstance(b := new.attributes.get(ATTR_BRIGHTNESS), (int, float))
            and b != old.attributes.get(ATTR_BRIGHTNESS)
        ):
            if not self._recently_commanded(new.entity_id, 10) and not self._lamp_dimmed(new.entity_id):
                if new.entity_id not in self._hand_set:
                    self._dbg("info", "brightness_by_hand", [new.entity_id], pct=round(b / 255 * 100))
                self._hand_set.add(new.entity_id)
            self._maybe_learn_brightness(new.entity_id)
        if not any(
            (s := self.hass.states.get(e)) is not None and s.state == STATE_ON
            for e in self._members
        ):
            self._on_by_motion = False  # turned off (by anyone): motion timer no longer ours
        self._track_session()
        self._recompute()
        self._check_idle()
        self.async_write_ha_state()

    def _recently_commanded(self, entity_id: str, seconds: float = 5) -> bool:
        """RoomControl itself switched this lamp on a moment ago (it already sent
        the right brightness and colour)."""
        wanted = self.hass.data.get(DOMAIN, {}).get("wanted", {}).get(entity_id) or {}
        at = wanted.get("at")
        return bool(at) and (dt_util.utcnow() - at).total_seconds() < seconds

    @callback
    def _on_config_updated(self) -> None:
        self._subscribe()
        self._apply_motion_config_change()
        self._apply_dim_config_change()
        self._check_idle()
        self.async_write_ha_state()

    def _dim_bundle_lamps(self) -> set[str]:
        """Lamps whose bundle takes part in Dim ("Doet mee met Dim", default yes)."""
        return set(self._lamps_where("dim", True))

    @callback
    def _apply_dim_config_change(self) -> None:
        """A bundle's "Doet mee met Dim" was switched in the panel while the room
        is on Dim: switched on → its lamps that are on go to the Dim level;
        switched off → they get their brightness from before back."""
        now = self._dim_bundle_lamps()
        prev, self._prev_dim_lamps = self._prev_dim_lamps, now
        if prev is None or now == prev or not self._dim_room:
            return
        dimmed = self._dimmed_lamps()  # minus alarm clock lamps, plus time-slot Dim
        entering = (now - prev) & dimmed
        leaving = (prev - now) - dimmed
        if entering or leaving:
            self.hass.async_create_task(self._async_apply_dim(leaving, entering))

    @callback
    def _apply_motion_config_change(self) -> None:
        """A bundle's "on_motion" was switched in the panel:
        - switched off: its lamps that are on go off (unless a time slot or
          lux control keeps them on now — that would only switch them on again);
        - switched on: if there is motion now, its lamps go on, as motion would."""
        now = set(self._motion_lamps())
        prev, self._prev_motion_lamps = self._prev_motion_lamps, now
        if prev is None:
            return
        members = set(self._members)
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731

        removed = (prev - now) & members
        if removed:
            kept = set(self._evening_lamps()) | set(self._lux_lamps_now())
            off = [e for e in self._members if e in removed and e not in kept and is_on(e)]
            if off:
                by_motion = self._on_by_motion
                self._auto_off("motion_removed", lamps=off)
                # The other motion bundles keep their grace period.
                self._on_by_motion = by_motion and any(is_on(e) for e in now & members)

        added = (now - prev) & members
        if added and self._any_motion(switching=True):
            on = [e for e in self._members if e in added and self._motion_ok(e) and not is_on(e)]
            if on:
                self._on_by_motion = True
                self._auto_on("motion_added", by_motion=True, lamps=on)

    # ── rules ──────────────────────────────────────────────────────────────

    def _is_dark(self) -> bool:
        """Darker than the room's "dark from" lux (no sensor/threshold: always dark)."""
        room = self._room
        threshold = room.get(CONF_DARK_LUX)
        if threshold is None:
            threshold = room.get(CONF_TARGET_LUX) or 0  # older rooms
        if not room_lux_sensors(room) or not threshold or threshold <= 0:
            return True
        lux = room_lux(self.hass, room)
        return lux < threshold if lux is not None else True

    def _sun_entity(self) -> str:
        """The sun entity from the general settings (older rooms: their own)."""
        return self._settings().get(SETTING_SUN_ENTITY) or self._room.get(CONF_SUN_ENTITY) or "sun.sun"

    def _sun_down(self) -> bool:
        state = self.hass.states.get(self._sun_entity())
        return state is not None and state.state == "below_horizon"

    def _phase(self) -> str:
        """"light", "dusk" (schemer: sun lower than the general setting's
        elevation) or "dark" (donker: the sun has set)."""
        if self._sun_down():
            return "dark"
        state = self.hass.states.get(self._sun_entity())
        elevation = state.attributes.get("elevation") if state is not None else None
        limit = self._settings().get(SETTING_DUSK_ELEVATION, DUSK_ELEVATION_DEFAULT)
        if isinstance(elevation, (int, float)) and isinstance(limit, (int, float)) and elevation < limit:
            return "dusk"
        return "light"

    def _dusk_progress(self) -> float:
        """How far schemer is: 0 when it starts, 1 when the sun sets."""
        state = self.hass.states.get(self._sun_entity())
        elevation = state.attributes.get("elevation") if state is not None else None
        limit = self._settings().get(SETTING_DUSK_ELEVATION, DUSK_ELEVATION_DEFAULT)
        if not isinstance(elevation, (int, float)) or not isinstance(limit, (int, float)) or limit <= 0:
            return 1.0
        return min(1.0, max(0.0, (limit - elevation) / limit))

    @callback
    def _dusk_ramp(self) -> None:
        """Schemer without lux control: the bundles on from schemer go up
        step by step as the sun sinks (the sun entity updates its elevation)."""
        if self._manual or self._phase() != "dusk":
            return
        lux = set(self._lux_lamps_now())
        lamps = [
            e for e in self._evening_lamps()
            if e not in lux and self._dusk_bundle(e) and e not in self._hand_set
            and (st := self.hass.states.get(e)) is not None and st.state == STATE_ON
        ]
        levels = self._phase_levels(lamps)
        changed: dict[str, int] = {}
        for e, pct in levels.items():
            have = self.hass.states.get(e).attributes.get(ATTR_BRIGHTNESS)
            have_pct = round(have * 100 / 255) if isinstance(have, (int, float)) else None
            if have_pct is None or abs(have_pct - pct) >= 2:
                changed[e] = pct
        if changed:
            self._dbg("adjust", "dusk", list(changed), pct=max(changed.values()))
            self.hass.async_create_task(self._async_call("turn_on", lamps=list(changed), levels=changed))

    def _normal_pct(self, lamp: str) -> int:
        """The bundle's own level: its fixed level, its standard brightness, else 100%."""
        return self._fixed_levels().get(lamp) or self._default_pct_for(lamp) or 100

    def _dusk_target(self, lamp: str) -> int:
        """The level a schemer slot works up to: the bundle's own level."""
        return self._normal_pct(lamp)

    def _phase_levels(self, lamps: list[str]) -> dict[str, int]:
        """Brightness for bundles on from schemer (no lux control): from 0%
        when schemer starts slowly up to the slot's dim level at sunset, along
        with the sun; once it is dark their own level."""
        phase = self._phase()
        out: dict[str, int] = {}
        for e in lamps:
            if not self._dusk_bundle(e):
                continue
            if phase == "dusk":
                out[e] = max(1, round(self._dusk_target(e) * self._dusk_progress()))
            elif phase == "dark":
                out[e] = self._normal_pct(e)
        return out

    # ── what the time slots, the sun and the alarm ask for ─────────────────
    #
    # A bundle's time slot running:
    #   sun up, target lux on → lux control: lamps on/brighter/dimmer/off until
    #                            the target lux
    #   otherwise             → lamps burn at their bundle's level
    # No slot running: only motion switches on — when the sun is down, or with
    #   the sun up when the room is darker than "dark from"; off after the
    #   grace period. When a slot ends: off (unless motion keeps them on).
    # Alarm: armed home → off (unless there is motion), motion → on at Dim, off
    #   after the grace period; or (room option "no_motion") off, motion does
    #   nothing, the alarm clock / by hand still switch on; armed away → off,
    #   except bundles marked to keep following their time slots.

    def _alarm_mode(self) -> str:
        """'home', 'away' or 'normal' (disarmed / other / no alarm panel)."""
        state = self._alarm_state() if self._alarm_entity() else None
        if state == ALARM_ARMED_HOME:
            return "home"
        if state == ALARM_ARMED_AWAY:
            return "away"
        return "normal"

    def _alarm_blocked(self) -> set[str]:
        """Lamps that must stay off for the alarm: armed away, unless the room
        ignores armed away (then it keeps following its time slots)."""
        if self._alarm_mode() != "away" or self._room.get(CONF_AWAY_FOLLOW_SCHEDULE):
            return set()
        return {e for e in self._members if not self._bopt(e, CONF_AWAY_FOLLOW_SCHEDULE, False)}

    def _evening_lamps(self) -> list[str]:
        """Bundles whose time slot runs burn at their level (the slot wins over
        motion). During the day, bundles with lux control are left to the
        target lux instead (see _lux_lamps_now)."""
        if self._alarm_mode() == "home":
            return []
        blocked = self._alarm_blocked()
        lux = set(self._lux_lamps_now())
        return [e for e in self._own_active() if e not in blocked and e not in lux]

    def _lux_lamps_now(self) -> list[str]:
        """Time slot running, sun up, target lux on: lamps lux control drives now."""
        room = self._room
        if (
            self._alarm_mode() == "home" or self._sun_down()
            or self._target_lux() <= 0 or not room_lux_sensors(room) or self._lux_paused_by_alarm()
        ):
            return []
        blocked = self._alarm_blocked()
        # Lamps of bundles whose time slot runs.
        sched = set(self._own_active())
        if not sched:
            return []
        clocks = self.hass.data.get(DOMAIN, {}).get("clocks")
        waking = clocks.lamps_ringing(self._area_id) if clocks is not None else set()  # a clock sets these
        phase = self._phase()
        # Lux-controlled bundles, plus during schemer the bundles on from schemer
        # (with a lux sensor they work towards the target lux).
        lamps = set(self._lux_control_lamps())
        if phase == "dusk":
            lamps |= {e for e in sched if self._dusk_bundle(e)}
        return [
            e for e in self._members
            if e in lamps and e in sched and e not in blocked and e not in waking
        ]

    def _motion_ok(self, lamp: str) -> bool:
        """May motion (or the door) switch `lamp` on now?"""
        if self._alarm_mode() == "home":
            # armed home: motion only, at Dim — or not at all (no_motion)
            return not self._armed_home_no_motion()
        if lamp in self._alarm_blocked():
            return False
        if lamp in self._evening_lamps() or lamp in self._lux_lamps_now():
            return False  # a time slot decides these now (it wins over motion)
        # No slot running: motion switches on —
        # with the sun up only when the room is darker than "dark from" (no lux
        # sensor or no threshold: always).
        return self._sun_down() or self._is_dark()

    def _bundle_names(self, lamps: list[str] | set[str] | None) -> list[str]:
        """Names of the bundles these lamps are in (a lamp outside a bundle: its own name)."""
        if lamps is None:
            lamps = list(self._members)
        names: list[str] = []
        groups = self._room.get(CONF_GROUPS, []) or []
        for e in lamps:
            for index, group in enumerate(groups):
                if e in (group.get("lights") or []):
                    name = (group.get("name") or "").strip() or f"Lichtbundel {index + 1}"
                    break
            else:
                st = self.hass.states.get(e)
                name = (st.attributes.get("friendly_name") if st else None) or e
            if name not in names:
                names.append(name)
        return names

    @callback
    def _dbg(self, kind: str, reason: str, lamps: list[str] | set[str] | None = None, **detail: Any) -> None:
        """Remember a decision for the panel's debug log (kind: on, off, ignored,
        blocked, adjust, info)."""
        self._debug.append({
            "at": dt_util.utcnow().isoformat(),
            "kind": kind,
            "reason": reason,
            "bundles": self._bundle_names(lamps) if lamps is not None or kind in ("on", "off") else [],
            **{k: v for k, v in detail.items() if v is not None},
        })

    def debug_log(self) -> list[dict[str, Any]]:
        """The debug log, newest first."""
        return list(reversed(self._debug))

    def upcoming(self, hours: int = 24) -> list[dict[str, Any]]:
        """What RoomControl expects to do in this room in the next `hours`
        (panel "Straks"): time slots starting/ending (and their Dim time),
        curtains opening/closing, All dim, alarm clocks and the grace period.
        [{"at": iso, "kind": ..., "names": [...]}], soonest first."""
        now = dt_util.now()
        until = now + timedelta(hours=hours)
        events: list[tuple[datetime, str, list[str]]] = []
        sun = self.hass.states.get(self._sun_entity())

        def sun_at(attr: str) -> datetime | None:
            value = sun.attributes.get(attr) if sun is not None else None
            parsed = dt_util.parse_datetime(value) if isinstance(value, str) else None
            return dt_util.as_local(parsed) if parsed else None

        def at_time(hm: Any, day: datetime) -> datetime | None:
            minutes = hm_minutes(hm)
            if minutes is None:
                return None
            return day.replace(hour=minutes // 60, minute=minutes % 60, second=0, microsecond=0)

        def add(when: datetime | None, kind: str, names: list[str]) -> None:
            if when is not None and now <= when <= until:
                events.append((when, kind, names))

        def slot_events(slots: list[dict[str, Any]], on: str, off: str, dim: str | None, names: list[str]) -> None:
            for slot in slots:
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
                    add(begin, on, names)
                    if end.get("type") == "sunrise":
                        add(sun_at("next_rising") if offset in (0, -1) else None, off, names)
                    else:
                        stop = at_time(end.get("time"), day)
                        if stop is not None and begin is not None and stop <= begin:
                            stop += timedelta(days=1)
                        add(stop, off, names)
                    if dim and slot.get("dim_at"):
                        moment = at_time(slot["dim_at"], day)
                        if moment is not None and begin is not None and moment < begin:
                            moment += timedelta(days=1)
                        add(moment, dim, names)

        # Time slots of light bundles with own times.
        groups = self._room.get(CONF_GROUPS, []) or []
        for index, group in enumerate(groups):
            lamps = [e for e in group.get("lights", []) or [] if e in self._members]
            if not lamps or not self._bopt(lamps[0], "own_times", False):
                continue
            name = (group.get("name") or "").strip() or f"Lichtbundel {index + 1}"
            slot_events(self._mode_slots(lamps[0]), "slot_on", "slot_off", "slot_dim", [name])
        # Curtains that follow dark/light.
        if self._following_covers():
            open_at = self._covers_open_at()
            if open_at is not None and open_at[0] == "time":
                for offset in (0, 1):
                    add(at_time("%02d:%02d" % divmod(open_at[1], 60), now + timedelta(days=offset)), "covers_open", [])
            elif open_at is not None:
                add(sun_at("next_rising"), "covers_open", [])
            close_at = self._room.get(CONF_COVERS_CLOSE_AT)
            add(sun_at("next_dusk" if close_at == "dusk" else "next_setting"), "covers_close", [])
        # All dim (general settings), when this room takes part.
        if self.follows_dim and self._members:
            from .switch import all_dim_slots  # here: avoids an import cycle

            vacation = self.hass.data.get(DOMAIN, {}).get("vacation")
            slot_events(mode_slots(all_dim_slots(self.hass), vacation), "all_dim_on", "all_dim_off", None, [])
        # Alarm clocks of this room.
        clocks = self.hass.data.get(DOMAIN, {}).get("clocks")
        if clocks is not None:
            for key, state in getattr(clocks, "states", {}).items():
                if key.startswith(f"{self._area_id}:") and state.next is not None:
                    found = clocks.find(key)
                    name = (found[2].get("name") or found[2].get("time") or "") if found else ""
                    add(dt_util.as_local(state.next), "clock", [name] if name else [])
        # The running grace period.
        if self._grace_until is not None:
            add(dt_util.as_local(self._grace_until), "grace_off", self._bundle_names(self._idle_lamps()))
        events.sort(key=lambda e: e[0])
        seen: set[tuple[str, str, tuple[str, ...]]] = set()
        out = []
        for when, kind, names in events:
            mark = (when.isoformat(timespec="minutes"), kind, tuple(names))
            if mark not in seen:
                seen.add(mark)
                out.append({"at": when.isoformat(), "kind": kind, "names": names})
        return out[:8]

    def debug_now(self) -> dict[str, Any]:
        """What RoomControl sees right now and, per bundle, what it wants."""
        room = self._room
        sun = self.hass.states.get(self._sun_entity())
        evening = set(self._evening_lamps())
        lux_now = set(self._lux_lamps_now())
        blocked = self._alarm_blocked()
        lux_ctrl = set(self._lux_control_lamps())
        motion_lamps = set(self._motion_lamps())
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
        bundles = []
        for index, group in enumerate(room.get(CONF_GROUPS, []) or []):
            lamps = [e for e in group.get("lights", []) or [] if e in self._members]
            if not lamps:
                continue
            first = lamps[0]
            if first in blocked:
                wants = "off_away"
            elif self._armed_home_no_motion():
                wants = "armed_home_no_motion"
            elif self._alarm_mode() == "home":
                wants = "motion_1pct"
            elif first in evening:
                wants = "on_slot"
            elif first in lux_now:
                wants = "lux"
            elif first in motion_lamps and self._motion_ok(first):
                wants = "motion"
            else:
                wants = "nothing"
            bundles.append({
                "name": (group.get("name") or "").strip() or f"Lichtbundel {index + 1}",
                "on": any(is_on(e) for e in lamps),
                "lux_control": first in lux_ctrl,
                "on_motion": first in motion_lamps,
                "wants": wants,
            })
        lux = room_lux(self.hass, room) if room_lux_sensors(room) else None
        return {
            "sun_entity": self._sun_entity(),
            "sun_state": sun.state if sun else None,
            "sun_down": self._sun_down(),
            "alarm": self._alarm_mode(),
            "someone_home": presence_allows(self.hass, room),
            "manual": self._manual,
            "lux": round(lux) if lux is not None else None,
            "dark_from": room.get(CONF_DARK_LUX),
            "target_lux": self._target_lux(),
            "motion": self._any_motion(),
            "bundles": bundles,
            "locks": self._debug_locks(),
            "doors": [
                {
                    "name": (st.attributes.get("friendly_name") if st else None) or d,
                    "state": st.state if st else None,
                    "since": st.last_changed.isoformat() if st else None,
                }
                for d in room.get(CONF_DOOR_SENSORS, []) or [] if d
                for st in [self.hass.states.get(d)]
            ],
        }

    def _debug_locks(self) -> list[dict[str, Any]]:
        manager = self.hass.data.get(DOMAIN, {}).get("locks")
        now = dt_util.utcnow()
        out = []
        for lock in room_locks(self._room):
            st = self.hass.states.get(lock["entity_id"])
            out.append({
                "name": (st.attributes.get("friendly_name") if st else None) or lock["entity_id"],
                "state": st.state if st else None,
                "since": st.last_changed.isoformat() if st else None,
                **(manager.lock_info(self._area_id, lock, now) if manager else {}),
            })
        return out

    @callback
    def _auto_on(
        self, reason: str, by_motion: bool = False, lamps: list[str] | None = None,
        levels: dict[str, int] | None = None,
    ) -> None:
        """Switch lamps on automatically; `levels`: brightness % per lamp
        (schemer/donker levels), also for lamps that are on already."""
        if self._manual:
            self._dbg("blocked", reason, lamps, why="manual")
            return  # manual control: RoomControl does nothing
        if not by_motion and self._armed_home_motion_only():
            self._dbg("blocked", reason, lamps, why="armed_home")
            return  # armed home, motion only: dusk etc. switch nothing on
        if by_motion and self._armed_home_no_motion():
            self._dbg("blocked", reason, lamps, why="armed_home_no_motion")
            return  # armed home, not on motion: motion switches nothing on
        lamps = list(self._members) if lamps is None else [e for e in lamps if e in self._members]
        wanted = list(lamps)
        blocked = self._alarm_blocked()
        lamps = [e for e in lamps if e not in blocked]
        if blocked & set(wanted):
            self._dbg("blocked", reason, sorted(blocked & set(wanted)), why="armed_away")
        # Motion only needs someone home.
        if by_motion:
            lamps = lamps if presence_allows(self.hass, self._room) else []
        else:
            lamps = self.lamps_allowed(lamps)
        if not lamps:
            if wanted and not (blocked and set(wanted) <= blocked):
                why = "nobody_home"
                self._dbg("blocked", reason, wanted, why=why)
            return
        if self._hand_set:
            # Set by hand and still on: keep the person's brightness.
            if levels:
                levels = {e: v for e, v in levels.items() if e not in self._hand_set}
            lamps = [e for e in lamps if not (e in self._hand_set and self._is_on(e))]
            if not lamps:
                return
        self._dbg("on", reason, lamps)
        _LOGGER.debug("%s: turning on %s (%s)", self.entity_id, lamps, reason)
        self.hass.async_create_task(self._async_call("turn_on", lamps=lamps, levels=levels))

    def _late_home_holds(self) -> bool:
        """A "Later thuis" switch is on and this room keeps its bundles on for it."""
        data = self.hass.data.get(DOMAIN, {})
        # Also right after someone came home in the dark (alarm → Someone comes home).
        return bool(self._room.get(CONF_LATE_HOME)) and bool(
            data.get("late_home_active") or data.get("arrive_active")
        )

    @callback
    def _on_late_home(self) -> None:
        """A "Later thuis" switch changed (or the sun set). Switched on and the
        sun down: the room's bundles go on (and stay on). Once none holds the room any more: off again (the off
        that was held back)."""
        if self._late_home_holds():
            # Only when it is dark (sun down); switched on during the day, they go on at sunset.
            if not self._late_on_done and not self._manual and self._sun_down():
                self._late_on_done = True
                off = [
                    e for e in self._members
                    if (st := self.hass.states.get(e)) is not None and st.state not in (STATE_ON, "unavailable", "unknown")
                ]
                if off:
                    # Straight to the lamps: presence and alarm don't stop this.
                    self._dbg("on", "late home", off)
                    self._late_pending = True
                    self.hass.async_create_task(self._async_call("turn_on", lamps=off))
            return
        self._late_on_done = False
        if not self._late_pending:
            return
        self._late_pending = False
        held = set(self._evening_lamps()) | set(self._lux_lamps_now())
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
        lamps = [e for e in self._members if is_on(e) and e not in held]
        if lamps and not (self._any_motion() and presence_allows(self.hass, self._room)):
            self._auto_off("late home: arrived", lamps=lamps)
        self._check_idle()
        self._recompute()
        self.async_write_ha_state()

    @callback
    def _auto_off(self, reason: str, lamps: list[str] | None = None) -> None:
        lamps = list(self._members) if lamps is None else [e for e in lamps if e in self._members]
        if lamps and not self._manual and self._late_home_holds():
            # Someone comes home later: the bundles stay on until they are home.
            self._late_pending = True
            self._dbg("blocked", reason, lamps, why="late_home")
            return
        if not lamps or self._manual:
            if lamps and self._manual:
                self._dbg("blocked", reason, lamps, why="manual")
            return
        self._dbg("off", reason, lamps)
        _LOGGER.debug("%s: turning off %s (%s)", self.entity_id, lamps, reason)
        self._on_by_motion = False
        self.hass.async_create_task(self._async_call("turn_off", lamps=lamps))

    @callback
    def _keep_evening_on(self, reason: str = "time slot, sun down") -> bool:
        """Time slot running and sun down: its bundles are
        always on — motion, the target lux etc. don't matter then. A bundle
        that is off (switched off by hand, a wall switch, …) goes on again.
        Not during manual control, armed home/away or with nobody home."""
        phase = self._phase()
        if self._manual or self._alarm_mode() == "home" or phase == "light":
            return False
        if not presence_allows(self.hass, self._room):
            return False
        # Donker: all of them; schemer: only bundles that are on from schemer.
        lamps = [
            e for e in self._evening_lamps()
            if phase == "dark" or self._dusk_bundle(e)
        ]
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
        off = [
            e for e in lamps
            if not is_on(e) and (st := self.hass.states.get(e)) is not None and st.state not in ("unavailable", "unknown")
        ]
        if not off:
            return False
        now = dt_util.utcnow()
        if self._evening_last_fix and (now - self._evening_last_fix).total_seconds() < 10:
            return False  # just did; don't fight a lamp that refuses
        self._evening_last_fix = now
        self._on_by_motion = False
        self._auto_on(reason, lamps=off, levels=self._phase_levels(off))
        return True

    @callback
    def _evening_tick(self, _now: Any = None) -> None:
        acted = self._evaluate_own_times()
        self._update_slot_dim()  # a time slot's Dim time
        if acted:
            self._recompute()
            self.async_write_ha_state()
        self._keep_evening_on()

    @callback
    def _setup_evening_check(self) -> None:
        wanted = bool(self._own_lamps())
        if wanted and self._cancel_evening_check is None:
            self._cancel_evening_check = async_track_time_interval(
                self.hass, self._evening_tick, timedelta(seconds=60)
            )
        elif not wanted and self._cancel_evening_check is not None:
            self._cancel_evening_check()
            self._cancel_evening_check = None

    @callback
    def _evaluate_conditions(self) -> bool:
        """Act on changes of sun phase and presence. At startup the room takes
        the state its running time slots ask for right away (sun down: the
        bundles on; sun up: lux control starts)."""
        room = self._room
        present = presence_allows(self.hass, room)
        key = (self._phase(), present)
        previous, self._conditions = self._conditions, key
        self._allowed = present
        if self._manual:
            return False
        if previous is None:
            self._dbg("info", "conditions", sun=key[0], home="yes" if present else "no")
            if self._alarm_mode() == "home" or not present:
                return False
            if self._phase() != "light" and self._keep_evening_on():
                return True
            lamps = self._evening_lamps()
            is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
            if lamps and not any(is_on(e) for e in lamps):
                self._auto_on("time slot", lamps=lamps, levels=self._phase_levels(lamps))
                return True
            if self._lux_lamps_now():
                self._regulate_lux(force=True)
            return False
        _was_phase, was_present = previous
        if previous != key:
            self._dbg("info", "conditions", sun=key[0], home="yes" if present else "no")
        if was_present and not present:
            self._auto_off("nobody home")
            return True
        return False

    @callback
    def _on_presence_change(self, _event: Event) -> None:
        self._evaluate_covers()
        self._evaluate_conditions()
        self._recompute()
        self._check_idle()
        self.async_write_ha_state()

    @callback
    # ── door sensors ───────────────────────────────────────────────────────

    def _door_lamps(self) -> list[str]:
        """Room lamps of the groups chosen for "door opens → lights on"."""
        room = self._room
        chosen = set(room.get(CONF_DOOR_GROUPS, []) or []) if room.get(CONF_DOOR_TURN_ON) else set()
        lamps: list[str] = []
        for group in room.get(CONF_GROUPS, []) or []:
            wanted = group["on_door"] if "on_door" in group else group.get("id") in chosen
            if wanted:
                lamps += [e for e in group.get("lights", []) if e in self._members and e not in lamps]
        return lamps

    @callback
    def _on_door_change(self, event: Event) -> None:
        """A door opened: switch on the chosen groups if it is dark enough."""
        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        if new is not None and old is not None and (new.state in DOOR_OPEN_STATES) != (old.state in DOOR_OPEN_STATES):
            self._dbg("door", "door_open" if new.state in DOOR_OPEN_STATES else "door_closed",
                      device=new.attributes.get("friendly_name") or new.entity_id)
        if new is None or new.state not in DOOR_OPEN_STATES:
            return
        if old is not None and old.state in DOOR_OPEN_STATES:
            return  # was already open
        room = self._room
        if self._manual or self._alarm_mode() == "home":
            return  # armed home: only motion
        lamps = [e for e in self._door_lamps() if self._motion_ok(e)]
        off = [e for e in lamps if (s := self.hass.states.get(e)) is None or s.state != STATE_ON]
        if not off or not presence_allows(self.hass, room):
            return
        self._dbg("on", "door", off)
        _LOGGER.debug("%s: door opened, turning on %s", self.entity_id, off)
        # Treated like motion: without further motion they go off after the grace period.
        self._on_by_motion = True
        self.hass.async_create_task(self._async_call("turn_on", lamps=off))

    @callback
    def _on_lock_change(self, event: Event) -> None:
        """A lock of the room changed: into the debug log (who did it is not known)."""
        old: State | None = event.data.get("old_state")
        new: State | None = event.data.get("new_state")
        if new is None or (old is not None and old.state == new.state):
            return
        if new.state in ("locking", "unlocking", "opening"):
            return  # only where it ends up
        self._dbg("lock", f"lock_state_{new.state}", device=new.attributes.get("friendly_name") or new.entity_id)

    # ── curtains ───────────────────────────────────────────────────────────

    def _following_covers(self) -> list[str]:
        """Curtains that follow dark/light: all of them (room option),
        or those in an older curtain group that follows."""
        room = self._room
        if room.get(CONF_COVERS_FOLLOW):
            return [c for c in room.get(CONF_COVERS, []) or [] if c]
        own = set(room.get(CONF_COVERS, []) or [])
        covers: list[str] = []
        for group in room.get(CONF_COVER_GROUPS, []) or []:
            if group.get("follow"):
                covers += [c for c in group.get("covers", []) if c in own and c not in covers]
        return covers

    def _covers_wanted_open(self) -> bool | None:
        """True = open, False = closed, None = no opinion (stay as they are).

        Closed in the evening per "close at" (dusk/dark); opened in the morning
        per "open at" (sunrise or a fixed time); without "open at" never opened
        automatically.
        """
        if self._covers_closed_time():
            return False
        # Only opened automatically when "open at" is chosen.
        return True if self._covers_open_at() is not None else None

    def _covers_open_at(self) -> tuple[str, int | None] | None:
        """("light", None), ("time", minutes after midnight) or None (not chosen)."""
        room = self._room
        open_at = room.get(CONF_COVERS_OPEN_AT)
        if open_at == "light":
            return "light", None
        if open_at == "time" and (minutes := hm_minutes(room.get(CONF_COVERS_OPEN_TIME))) is not None:
            return "time", minutes
        return None

    def _covers_closed_time(self) -> bool:
        """Is it a time for closed curtains? Evening: from dark — or schemer (room
        option "close at"). Morning: until "open at" (sunrise via the Sun
        integration, or a fixed time); not chosen: until it is light."""
        open_at = self._covers_open_at()
        if open_at is not None and open_at[0] == "time":
            now = dt_util.now()
            if now.hour * 60 + now.minute < open_at[1]:
                return True  # not yet the opening time
            if self._sun_rising():
                return False  # morning, opening time passed: open (even if still dark)
        elif open_at is not None and self._sun_rising():
            return self._sun_down()  # morning: closed until sunrise
        phase = self._phase()
        if phase == "dusk":
            return self._room.get(CONF_COVERS_CLOSE_AT) == "dusk"
        return phase == "dark"

    def _sun_rising(self) -> bool:
        """Morning (the sun is rising, per the Sun integration; else before noon)."""
        state = self.hass.states.get(self._sun_entity())
        rising = state.attributes.get("rising") if state is not None else None
        if isinstance(rising, bool):
            return rising
        return dt_util.now().hour < 12

    @callback
    def _setup_cover_time(self) -> None:
        """A fixed opening time: evaluate the curtains at that minute."""
        if self._cancel_cover_time:
            self._cancel_cover_time()
            self._cancel_cover_time = None
        open_at = self._covers_open_at()
        if open_at is None or open_at[0] != "time" or not self._following_covers():
            return

        @callback
        def _at_time(_now: Any) -> None:
            self._evaluate_covers()

        hour, minute = divmod(open_at[1], 60)
        self._cancel_cover_time = async_track_time_change(self.hass, _at_time, hour=hour, minute=minute, second=1)

    @callback
    def _evaluate_covers(self) -> None:
        """Open/close following curtains when what is wanted changes.

        The first evaluation only remembers the wanted state, so a restart or a
        config change never moves curtains; between changes they stay as the
        user left them.
        """
        wanted = self._covers_wanted_open()
        if not self._covers_init:
            self._covers_init = True
            self._covers_open = wanted
            return
        previous, self._covers_open = self._covers_open, wanted
        if wanted is None or wanted == previous or self._manual:
            return
        covers = self._following_covers()
        if not covers:
            return
        service = "open_cover" if wanted else "close_cover"
        _LOGGER.debug("%s: %s %s", self.entity_id, service, covers)
        self.hass.async_create_task(
            rc_call(self.hass,"cover", service, {ATTR_ENTITY_ID: covers}, blocking=True)
        )

    # ── lux control & standard brightness ──────────────────────────────────

    def _default_pct(self) -> int | None:
        value = self._room.get(CONF_DEFAULT_BRIGHTNESS)
        if not isinstance(value, (int, float)) or value <= 0:
            return None
        return int(min(100, max(1, value)))

    def _adjustable_on(self) -> list[str]:
        """Room lamps that are on and not pinned to a fixed level."""
        fixed = self._fixed_levels()
        return [
            e for e in self._members
            if e not in fixed and (s := self.hass.states.get(e)) is not None and s.state == STATE_ON
        ]

    def _target_lux(self) -> float:
        """The room's target lux; 0 when the target is switched off."""
        if not self._room.get(CONF_TARGET_LUX_ENABLED, True):
            return 0
        return self._room.get(CONF_TARGET_LUX) or 0

    def _lux_control_lamps(self) -> list[str]:
        """Lamps with lux control (none while the target lux is switched off)."""
        if not self._room.get(CONF_TARGET_LUX_ENABLED, True):
            return []
        return self._lamps_where("lux_control", self._room.get(CONF_LUX_CONTROL))

    def _lux_paused_by_alarm(self) -> bool:
        """The alarm is in a state for which this room pauses lux control."""
        states = self._room.get(CONF_LUX_CONTROL_OFF_ALARM) or []
        return bool(states) and bool(self._alarm_entity()) and self._alarm_state() in states

    @callback
    def _setup_lux_control(self) -> None:
        room = self._room
        sensors = room_lux_sensors(room)
        wanted = bool(self._lux_control_lamps() and sensors and self._target_lux() > 0)
        self._track("lux", sensors if wanted else [], self._on_lux_change)
        if wanted and self._cancel_lux_interval is None:
            self._cancel_lux_interval = async_track_time_interval(
                self.hass, self._lux_tick, timedelta(seconds=LUX_CONTROL_INTERVAL)
            )
        elif not wanted and self._cancel_lux_interval is not None:
            self._cancel_lux_interval()
            self._cancel_lux_interval = None

    @callback
    def _on_lux_change(self, _event: Event) -> None:
        self._regulate_lux()

    @callback
    def _lux_tick(self, now: datetime | None = None) -> None:
        self._regulate_lux(now)

    @callback
    def _regulate_lux(self, now: datetime | None = None, force: bool = False) -> None:
        """Schedule on, sun up: bring the room to the target lux. Too dark → lamps
        on and gradually brighter; too light → gradually dimmer, and off when
        the lamps no longer make a difference (lowest level, still too light)."""
        room = self._room
        lamps = self._lux_lamps_now()
        if not lamps or self._manual or not presence_allows(self.hass, room):
            return
        target = self._target_lux()
        lux = room_lux(self.hass, room)
        if target <= 0 or lux is None:
            return
        now = now or dt_util.utcnow()
        if not force and self._lux_last_adjust and (now - self._lux_last_adjust).total_seconds() < LUX_CONTROL_MIN_GAP:
            return
        if abs(lux - target) <= target * LUX_CONTROL_DEADBAND:
            return
        is_on = lambda e: (st := self.hass.states.get(e)) is not None and st.state == STATE_ON  # noqa: E731
        on = [e for e in lamps if is_on(e)]
        off = [e for e in lamps if not is_on(e)]
        fixed = self._fixed_levels()
        # Set by hand: brightness and on/off stay as the person left them.
        on = [e for e in on if e not in self._hand_set]
        adjustable = [e for e in on if e not in fixed and not self._lamp_dimmed(e)]
        levels = [
            b for e in adjustable
            if isinstance(b := self.hass.states.get(e).attributes.get(ATTR_BRIGHTNESS), (int, float))
        ]
        current = sum(levels) / len(levels) if levels else 255
        # Lux control never makes lamps brighter than their bundle's maximum.
        caps = [self._auto_max_pct(e) or 100 for e in adjustable]
        cap = round(min(caps) * 255 / 100) if caps else 255
        self._learn_lux_gain(lux, current, adjustable)
        if lux < target:
            if off:
                # Too dark: switch the lamps on, starting low.
                self._lux_last_adjust = now
                self._lux_min_asked = None
                self._dbg("on", "lux_dark", off, lux=round(lux), target=round(target))
                _LOGGER.debug("%s: lux %s < target %s, switching on %s", self.entity_id, lux, target, off)
                start = min([LUX_CONTROL_START_PCT, *[self._auto_max_pct(e) or 100 for e in off if e not in fixed]])
                data = {ATTR_ENTITY_ID: [e for e in off if e not in fixed], "brightness_pct": start}
                if data[ATTR_ENTITY_ID]:
                    self.hass.async_create_task(rc_call(self.hass, "light", "turn_on", data, blocking=True))
                if pinned := [e for e in off if e in fixed]:
                    self.hass.async_create_task(self._async_call("turn_on", lamps=pinned))
                return
            if not adjustable:
                return
            factor = (target / lux) if lux > 0 else 1 + LUX_CONTROL_MAX_STEP
        else:
            if not on:
                return
            at_min = self._lux_min_asked is not None and self._lux_min_asked == tuple(sorted(adjustable))
            if not adjustable or current <= LUX_CONTROL_MIN_BRIGHTNESS or at_min:
                # Lowest level and still too light: the lamps make no difference → off.
                self._lux_min_asked = None
                self._lux_last_adjust = now
                self._dbg("off", "lux_bright", on, lux=round(lux), target=round(target))
                _LOGGER.debug("%s: lux %s > target %s at the lowest level, switching off", self.entity_id, lux, target)
                self.hass.async_create_task(
                    rc_call(self.hass, "light", "turn_off", {ATTR_ENTITY_ID: on}, blocking=True)
                )
                return
            factor = target / lux
        if self._lux_gain:
            # Known lux per brightness step: go (almost) straight to the target.
            step = max(-LUX_MODEL_MAX_STEP, min(LUX_MODEL_MAX_STEP, (target - lux) / self._lux_gain))
            new = int(round(min(255, max(LUX_CONTROL_MIN_BRIGHTNESS, current + step))))
        else:
            factor = min(1 + LUX_CONTROL_MAX_STEP, max(1 - LUX_CONTROL_MAX_STEP, factor))
            new = int(round(min(255, max(LUX_CONTROL_MIN_BRIGHTNESS, current * factor))))
        if lux < target:
            # Brighter, but not above the maximum; set brighter by hand: leave it.
            new = min(new, cap)
            if new <= round(current):
                return
            self._lux_min_asked = None
        else:
            # Too light: always a noticeable step down (a tiny step would round
            # to no change and leave the lamps too bright for good).
            new = max(LUX_CONTROL_MIN_BRIGHTNESS, min(new, round(current) - max(3, round(current * 0.05))))
            self._lux_min_asked = tuple(sorted(adjustable)) if new <= LUX_CONTROL_MIN_BRIGHTNESS else None
        if new == round(current):
            return  # already at the limit (e.g. full brightness and still too dark)
        self._lux_probe = (lux, current, tuple(sorted(adjustable)))
        self._lux_last_adjust = now
        self._dbg("adjust", "lux_brighter" if new > current else "lux_dimmer", adjustable,
                  lux=round(lux), target=round(target), pct=round(new / 255 * 100))
        _LOGGER.debug("%s: lux %s → target %s, brightness %s → %s", self.entity_id, lux, target, current, new)
        self.hass.async_create_task(
            rc_call(self.hass, "light", "turn_on", {ATTR_ENTITY_ID: adjustable, ATTR_BRIGHTNESS: new}, blocking=True)
        )

    def _lux_now(self) -> int | None:
        lux = room_lux(self.hass, self._room) if room_lux_sensors(self._room) else None
        return round(lux) if lux is not None else None

    def _motion_sensors(self) -> list[str]:
        """Own sensors plus those of linked rooms: motion anywhere in the group counts."""
        return group_motion_sensors(self.hass, self._area_id)

    def _any_motion(self, switching: bool = False) -> bool:
        """Motion on any sensor of the group. switching: only sensors inside their
        time window count (outside it a sensor does not switch lights on, but its
        motion still keeps lights that are on from going off)."""
        return any(
            (s := self.hass.states.get(e)) is not None and s.state in MOTION_ON_STATES
            and (not switching or self._sensor_in_window(e))
            for e in self._motion_sensors()
        )

    def _sensor_in_window(self, sensor: str) -> bool:
        """One of the sensor's time slots runs now (or it has none: always).
        Vacation slots count in vacation mode, as for light bundles."""
        slots = motion_slots(self.hass, sensor)
        if slots is None:
            return True
        slots = mode_slots(slots, self.hass.data.get(DOMAIN, {}).get("vacation"))
        now, phase = dt_util.as_local(dt_util.now()), self._phase()
        return any(self._slot_part(slot, now, phase) is not None for slot in slots)

    @callback
    def _on_motion_change(self, event: Event) -> None:
        """Any sensor on → lights on; only when all are off does the timer start."""
        new: State | None = event.data.get("new_state")
        if new is None:
            return
        if new.entity_id in room_motion_sensors(self._room):
            self._own_motion_seen(new.state in MOTION_ON_STATES)
        if new.state in MOTION_ON_STATES:
            reason = self._motion_block_reason()
            if reason is None and not self._sensor_in_window(new.entity_id):
                reason = "outside_window"  # this sensor does not switch lights on now
            if reason is None:
                self._on_by_motion = True
                off = [
                    e for e in self._motion_lamps()
                    if self._motion_ok(e) and ((st := self.hass.states.get(e)) is None or st.state != STATE_ON)
                ]
                self._auto_on("motion", by_motion=True, lamps=off)
            else:
                self._dbg("ignored", "motion", why=reason, lux=self._lux_now())
                _LOGGER.debug("%s: motion ignored (%s)", self.entity_id, reason)
            self._motion_note = reason
            self._recompute()
            self.async_write_ha_state()
        self._check_idle()
        self._fan_update()

    # ── smart options ──────────────────────────────────────────────────────

    def _learn(self) -> LearnStore | None:
        return self.hass.data.get(DOMAIN, {}).get("learn")

    def _is_on(self, entity_id: str) -> bool:
        return (st := self.hass.states.get(entity_id)) is not None and st.state == STATE_ON

    def _smart_attrs(self) -> dict[str, Any]:
        """What the smart options learned / do now (panel)."""
        learn = self._learn()
        room = self._room
        return {
            "grace_extra": learn.grace_extra(self._area_id) if learn else 0,
            "media_active": self._media_active(),
            "last_motion_hold": round(self._last_motion_hold_left()),
            "lux_gain": round(self._lux_gain, 2) if self._lux_gain else None,
            "learned_brightness": learn.learned_count(self._area_id) if learn and room.get(CONF_LEARN_BRIGHTNESS) else 0,
            "replay_days": learn.session_days(self._area_id) if learn and room.get(CONF_AWAY_REPLAY) else 0,
            "replay_active": self._replay_active(),
            "replay_lamps": sorted(self._replay_on),
            "motion_weeks": learn.motion_weeks(self._area_id) if learn and room.get(CONF_ANOMALY_ALERTS) else 0,
        }

    def _clock_attrs(self) -> dict[str, Any]:
        """The room's active alarm clocks (panel card): next ring, ringing now."""
        manager = self.hass.data.get(DOMAIN, {}).get("clocks")
        states = [
            st for key, st in (manager.states.items() if manager else [])
            if key.startswith(f"{self._area_id}:")
        ]
        nexts = [st.next for st in states if st.next]
        return {
            "clock_next": min(nexts).isoformat() if nexts else None,
            "clock_ringing": any(st.ringing for st in states),
        }

    @callback
    def restore_auto(self, lamps: list[str] | None = None) -> None:
        """Panel "herstel": forget the brightness set by hand; lamps that are
        on go back to the level RoomControl wants now."""
        lamps = [e for e in (lamps or self._members) if e in self._members]
        self._hand_set -= set(lamps)
        on = [e for e in lamps if self._is_on(e)]
        if on and not self._manual:
            lux = set(self._lux_lamps_now())
            levels = self._phase_levels([e for e in on if e not in lux])
            fixed = self._fixed_levels()
            for e in on:
                if e in lux or e in levels:
                    continue
                if (pct := fixed.get(e) or self._default_pct_for(e)) is not None:
                    levels[e] = pct
            if levels:
                self._dbg("adjust", "restore", list(levels))
                self.hass.async_create_task(self._async_call("turn_on", lamps=list(levels), levels=levels))
            if lux & set(on):
                self._regulate_lux(force=True)
        self._recompute()
        self.async_write_ha_state()

    @callback
    def refresh_state(self) -> None:
        self._recompute()
        self.async_write_ha_state()

    # Media keeps the room in use.

    def _media_players(self) -> list[str]:
        return [p for p in self._room.get(CONF_MEDIA_PLAYERS, []) or [] if p]

    def _media_active(self) -> bool:
        return bool(self._room.get(CONF_MEDIA_HOLD)) and any(
            (st := self.hass.states.get(p)) is not None and st.state in MEDIA_ACTIVE_STATES
            for p in self._media_players()
        )

    @callback
    def _on_media_change(self, _event: Event) -> None:
        self._check_idle()
        self._recompute()
        self.async_write_ha_state()

    # The last motion in the house was here.

    def _last_motion_hold_left(self) -> float:
        """Seconds the "last motion was here" hold still runs (0 = none)."""
        if not self._room.get(CONF_LAST_MOTION_HOLD):
            return 0
        last = self.hass.data.get(DOMAIN, {}).get("last_motion")
        if not last or last[0] not in linked_group(self.hass, self._area_id):
            return 0
        return max(0.0, LAST_MOTION_HOLD_MAX - (dt_util.utcnow() - last[1]).total_seconds())

    @callback
    def _on_last_motion(self) -> None:
        self._check_idle()
        self._recompute()
        self.async_write_ha_state()

    @callback
    def _hold_expired(self, _now: Any) -> None:
        self._cancel_hold = None
        self._check_idle()
        self._recompute()
        self.async_write_ha_state()

    @callback
    def _own_motion_seen(self, on: bool) -> None:
        """A sensor of this room itself changed: remember it for the smart options."""
        now = dt_util.utcnow()
        self._last_motion_at = now
        self._long_on_sent = False
        if not on:
            return
        data = self.hass.data.get(DOMAIN, {})
        previous = data.get("last_motion")
        data["last_motion"] = (self._area_id, now)
        if not previous or previous[0] != self._area_id:
            async_dispatcher_send(self.hass, SIGNAL_LAST_MOTION)
        learn = self._learn()
        if learn is None:
            return
        if self._idle_off_at is not None:
            seconds = (now - self._idle_off_at).total_seconds()
            self._idle_off_at = None
            if self._room.get(CONF_ADAPTIVE_GRACE):
                extra = learn.grace_feedback(self._area_id, seconds)
                if extra is not None:
                    self._dbg("info", "grace_learned", extra=extra, after=round(seconds))
        if learn.record_motion(self._area_id, now) and self._room.get(CONF_ANOMALY_ALERTS):
            self._notify("motion", "anomaly_motion")

    # Learned standard brightness.

    @callback
    def _maybe_learn_brightness(self, entity_id: str) -> None:
        """A lamp's brightness changed while on: learn it once it settled, if
        it was a person (not RoomControl, Dim or lux control)."""
        if (
            not self._room.get(CONF_LEARN_BRIGHTNESS) or self._manual
            or self._recently_commanded(entity_id, 10) or self._lamp_dimmed(entity_id)
            or entity_id in self._fixed_levels() or entity_id in self._lux_lamps_now()
            or entity_id in self._replay_on
        ):
            return
        if cancel := self._bright_pending.pop(entity_id, None):
            cancel()

        @callback
        def _settled(_now: Any) -> None:
            self._bright_pending.pop(entity_id, None)
            st = self.hass.states.get(entity_id)
            learn = self._learn()
            if (
                learn is None or st is None or st.state != STATE_ON
                or not isinstance(b := st.attributes.get(ATTR_BRIGHTNESS), (int, float))
                or self._recently_commanded(entity_id, BRIGHT_SETTLE + 5)
            ):
                return
            learn.record_brightness(self._area_id, entity_id, dt_util.now().hour, b / 255 * 100)
            self._dbg("info", "brightness_learned", [entity_id], pct=round(b / 255 * 100))

        self._bright_pending[entity_id] = async_call_later(self.hass, BRIGHT_SETTLE, _settled)

    # Lux model.

    @callback
    def _learn_lux_gain(self, lux: float, current: float, adjustable: list[str]) -> None:
        """After an adjustment: how much lux did the brightness change bring?"""
        probe, self._lux_probe = self._lux_probe, None
        if probe is None or probe[2] != tuple(sorted(adjustable)):
            return
        delta_b = current - probe[1]
        if abs(delta_b) < 5:
            return
        sample = (lux - probe[0]) / delta_b
        if not 0.05 <= sample <= 50:
            return  # daylight changed more than the lamps did: no use
        self._lux_gain = sample if self._lux_gain is None else self._lux_gain * 0.6 + sample * 0.4

    # Sessions and replay.

    @callback
    def _track_session(self) -> None:
        """Remember when the room's lamps were on (for replay)."""
        on = {e for e in self._members if self._is_on(e)}
        now = dt_util.utcnow()
        if on and self._session_start is None:
            self._session_start = now
            self._session_lamps = set(on)
            # Replayed or nobody home: not how the room is really used.
            self._session_skip = bool(self._replay_on) or not anyone_home(self.hass)
        elif on:
            self._session_lamps |= on
        elif self._session_start is not None:
            if not self._session_skip and (learn := self._learn()) is not None:
                learn.record_session(self._area_id, self._session_start, now, sorted(self._session_lamps))
            self._session_start = None
            self._session_lamps = set()
        if not on:
            self._replay_on = set()

    def _replay_active(self) -> bool:
        return (
            bool(self._room.get(CONF_AWAY_REPLAY)) and not self._manual and bool(self._members)
            and (self._alarm_mode() == "away" or not anyone_home(self.hass))
            and self._sun_down()
        )

    @callback
    def _setup_smart_tick(self) -> None:
        wanted = bool(self._room.get(CONF_AWAY_REPLAY) or self._room.get(CONF_ANOMALY_ALERTS))
        if wanted and self._cancel_smart_tick is None:
            self._cancel_smart_tick = async_track_time_interval(
                self.hass, self._smart_tick, timedelta(seconds=60)
            )
        elif not wanted and self._cancel_smart_tick is not None:
            self._cancel_smart_tick()
            self._cancel_smart_tick = None

    @callback
    def _smart_tick(self, _now: Any = None) -> None:
        self._replay_step()
        self._long_on_check()

    @callback
    def _replay_step(self) -> None:
        learn = self._learn()
        if learn is None:
            return
        if not self._replay_active():
            if self._replay_on and not self._manual and not anyone_home(self.hass):
                # Still nobody home (e.g. the sun came up): the replayed lamps go off.
                lamps = [e for e in self._replay_on if self._is_on(e)]
                if lamps:
                    self._dbg("off", "replay_end", lamps)
                    self.hass.async_create_task(self._async_call("turn_off", lamps=lamps))
            self._replay_on = set()
            return
        wanted = learn.replay_lamps(self._area_id, dt_util.utcnow()) & set(self._members)
        to_on = sorted(e for e in wanted if not self._is_on(e))
        to_off = sorted(e for e in self._replay_on - wanted if self._is_on(e))
        if to_on:
            self._replay_on |= set(to_on)
            self._dbg("on", "replay", to_on)
            self.hass.async_create_task(self._async_call("turn_on", lamps=to_on))
        if to_off:
            self._replay_on -= set(to_off)
            self._dbg("off", "replay", to_off)
            self.hass.async_create_task(self._async_call("turn_off", lamps=to_off))
        if to_on or to_off:
            self._recompute()
            self.async_write_ha_state()

    # Notifications.

    @callback
    def _long_on_check(self) -> None:
        """Lights on for hours without motion, while nothing holds them on."""
        if not self._room.get(CONF_ANOMALY_ALERTS) or self._long_on_sent or self._manual:
            return
        if not room_motion_sensors(self._room) or self._any_motion():
            return
        held = set(self._evening_lamps()) | set(self._lux_lamps_now()) | self._replay_on
        on = [e for e in self._members if self._is_on(e) and e not in held]
        if not on or self._media_active():
            return
        if dt_util.utcnow() - self._last_motion_at >= timedelta(hours=ANOMALY_LIGHTS_ON_HOURS):
            self._long_on_sent = True
            self._notify("lights_on", "anomaly_lights_on", lamps=on)

    @callback
    def _notify(self, kind: str, reason: str, lamps: list[str] | None = None) -> None:
        now = dt_util.utcnow()
        last = self._anomaly_sent.get(kind)
        if last is not None and now - last < ANOMALY_REPEAT:
            return
        self._anomaly_sent[kind] = now
        area = ar.async_get(self.hass).async_get_area(self._area_id)
        name = area.name if area else self._area_id
        if kind == "motion":
            message = text(self.hass, "anomaly_motion", room=name)
        else:
            message = text(self.hass, "anomaly_lights_on", room=name, hours=ANOMALY_LIGHTS_ON_HOURS)
        self._dbg("info", reason, lamps)
        persistent_notification.async_create(
            self.hass, message, title="RoomControl", notification_id=f"roomcontrol_{self._area_id}_{kind}"
        )
        self.hass.bus.async_fire(
            "roomcontrol_anomaly", {"area_id": self._area_id, "kind": kind, "message": message}
        )

    # ── fan ────────────────────────────────────────────────────────────────

    def _fans(self) -> list[str]:
        """Own fans plus the fans shared with other rooms."""
        return room_fans(self.hass, self._area_id)

    def _fan_steps(self) -> list[tuple[float, int]]:
        """Valid steps as (minutes, percentage), sorted by minutes."""
        steps = []
        for step in room_fan_steps(self.hass, self._area_id):
            minutes, pct = step.get("minutes"), step.get("percentage")
            if isinstance(minutes, (int, float)) and isinstance(pct, (int, float)) and minutes >= 0:
                steps.append((float(minutes), int(min(100, max(0, pct)))))
        return sorted(steps)

    def _own_motion(self) -> bool:
        """Motion on this room's own sensors (linked rooms do not count here)."""
        return any(
            (s := self.hass.states.get(e)) is not None and s.state in MOTION_ON_STATES
            for e in room_motion_sensors(self._room)
        )

    @property
    def _activity_since(self) -> datetime | None:
        act = self._fan_activity()
        return act.since if act else None

    def _fan_activity(self) -> FanActivity | None:
        """The running activity of this room's (possibly shared) fans."""
        key = fan_key(self._fans())
        return fan_activities(self.hass).get(key) if key else None

    def _fan_activity_attrs(self) -> dict[str, Any]:
        act = self._fan_activity()
        return {
            "activity_since": act.since.isoformat() if act else None,
            "fan_percentage": act.pct if act else None,
            "fan_off_at": act.off_at.isoformat() if act and act.off_at else None,
            "fan_step": act.step if act else None,
            "fan_step_count": len(act.steps) if act else len(self._fan_steps()),
        }

    def _fan_rooms(self) -> list[RoomControlLight]:
        """Room entities sharing (some of) this room's fans, this one included."""
        fans = set(self._fans())
        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        rooms = [
            e for a in fan_group(self.hass, self._area_id)
            if (e := entities.get(a)) is not None and set(e._fans()) & fans
        ]
        return rooms if self in rooms else [self, *rooms]

    def _fan_motion_enabled(self) -> bool:
        """This room drives the fan by activity (motion)."""
        return bool(self._fans()) and bool(self._fan_steps()) and bool(self._room.get(CONF_FAN_MOTION, True))

    @callback
    def _fan_notify(self) -> None:
        """Show the (shared) activity on every room using these fans."""
        for room in self._fan_rooms():
            if room.entity_id:
                room.async_write_ha_state()

    @callback
    def _fan_update(self, write: bool = True) -> None:
        """Start/continue the shared activity while any room using these fans has
        motion; when none has, start the run-on time, after which the fans go off."""
        key = fan_key(self._fans())
        if self._fan_key is not None and self._fan_key != key:
            # The room's fans changed: end what ran on the old ones.
            self._fan_end_activity(self._fan_key)
        self._fan_key = key
        rooms = self._fan_rooms() if key else []
        if not key or not anyone_home(self.hass) or not any(r._fan_motion_enabled() for r in rooms):
            self._fan_stop_activity()  # nobody home / no activity control: fan stays off
            return
        acts = fan_activities(self.hass)
        act = acts.get(key)
        motion = any(r._fan_motion_enabled() and r._own_motion() for r in rooms)
        if motion:
            if act is None:
                steps = next((st for r in rooms if r._fan_motion_enabled() and (st := r._fan_steps())), [])
                act = acts[key] = FanActivity(since=dt_util.utcnow(), steps=steps)
                _LOGGER.debug("%s: fan activity started for %s", self.entity_id, key)
            elif not act.cancel_end and act.stepping:
                return  # already running, nothing changes
            act.cancel_end_timer()
            if not act.stepping:
                self._fan_schedule_steps(key, act)
        elif act is not None and act.cancel_end is None:
            # No motion in any of the rooms: no more steps, run on, then off.
            act.cancel_steps()
            run_on = max((r._fan_run_on() for r in rooms if r._fan_motion_enabled()), default=0)
            act.off_at = dt_util.utcnow() + timedelta(seconds=run_on)

            @callback
            def _end(_now: Any, k: FanKey = key) -> None:
                self._fan_end(k)

            act.cancel_end = async_call_later(self.hass, run_on, _end)
            _LOGGER.debug("%s: no motion, fans %s off in %ss", self.entity_id, key, run_on)
        else:
            return
        if write:
            self._fan_notify()

    @callback
    def _fan_schedule_steps(self, key: FanKey, act: FanActivity) -> None:
        """Plan the steps not reached yet, counted from the start of the activity."""
        elapsed = (dt_util.utcnow() - act.since).total_seconds()
        act.stepping = True
        for index, (minutes, pct) in enumerate(act.steps):
            if index < act.step:
                continue

            # Must be a @callback so HA runs it in the event loop.
            @callback
            def _fire(_now: Any, i: int = index, p: int = pct) -> None:
                self._fan_step(key, i, p)

            act.step_unsubs.append(async_call_later(self.hass, max(0.0, minutes * 60 - elapsed), _fire))

    @callback
    def _fan_step(self, key: FanKey, index: int, pct: int) -> None:
        """A step's time is reached: speed up (never down during activity)."""
        act = fan_activities(self.hass).get(key)
        if act is None or index < act.step:
            return
        act.step = index + 1
        if act.pct is None or pct > act.pct:
            act.pct = pct
        _LOGGER.debug("%s: fan step %s (%s%%)", self.entity_id, act.step, act.pct)
        if not self._manual:
            self._fan_apply()
        self._fan_notify()

    @callback
    def _fan_end(self, key: FanKey) -> None:
        """Run-on time over without motion: the activity ends, fans off."""
        self._fan_end_activity(key)
        self._fan_notify()

    @callback
    def _fan_end_activity(self, key: FanKey) -> None:
        act = fan_activities(self.hass).pop(key, None)
        if act is None:
            return
        act.cancel_all()
        _LOGGER.debug("%s: fan activity ended for %s", self.entity_id, key)
        if act.pct is not None:
            self._fan_apply(list(key), force_off=True)

    # ── fan by temperature ─────────────────────────────────────────────────

    def _fan_temp_config(self) -> tuple[str, float, int] | None:
        """(sensor, from temperature, speed %) when set up and the room has fans."""
        room = self._room
        sensor = room.get(CONF_FAN_TEMP_SENSOR)
        lo, speed = room.get(CONF_FAN_TEMP_MIN), room.get(CONF_FAN_TEMP_SPEED)
        if not sensor or not self._fans():
            return None
        if not all(isinstance(v, (int, float)) for v in (lo, speed)) or speed <= 0:
            return None
        return sensor, float(lo), int(min(100, speed))

    def _fan_temperature(self) -> float | None:
        config = self._fan_temp_config()
        state = self.hass.states.get(config[0]) if config else None
        try:
            return float(state.state) if state else None
        except ValueError:
            return None

    @callback
    def _setup_fan_temp(self) -> None:
        config = self._fan_temp_config()
        self._track("fan_temp", [config[0]] if config else [], self._on_fan_temp_change)
        # Nobody home → the fan stays off; someone comes home → temperature counts again.
        self._track("fan_persons", household_persons(self.hass) if self._fans() else [], self._on_fan_presence_change)
        self._fan_temp_eval(write=False)

    @callback
    def _on_fan_presence_change(self, _event: Event) -> None:
        if not anyone_home(self.hass) and self._activity_since is not None:
            self._fan_stop_activity()
        self._fan_temp_eval(write=False)
        self._recompute()
        if self.entity_id:
            self.async_write_ha_state()

    @callback
    def _on_fan_temp_change(self, _event: Event) -> None:
        self._fan_temp_eval()

    @callback
    def _fan_temp_eval(self, write: bool = True) -> None:
        """Temperature at or above the limit → the fan runs at the chosen speed."""
        config = self._fan_temp_config()
        temp = self._fan_temperature()
        if config is None or temp is None or not anyone_home(self.hass):
            wanted = None
        else:
            _, lo, speed = config
            # Already running: a little margin before it stops (no flapping).
            margin = FAN_TEMP_HYSTERESIS if self._fan_temp_pct is not None else 0.0
            wanted = speed if temp >= lo - margin else None
        if wanted == self._fan_temp_pct or self._manual:
            return
        _LOGGER.debug("%s: temperature %s → fan %s", self.entity_id, temp, wanted)
        self._fan_temp_pct = wanted
        self._fan_apply()
        if write and self.entity_id:
            self.async_write_ha_state()

    @callback
    def _fan_apply(self, fans: list[str] | None = None, force_off: bool = False) -> None:
        """Drive the (possibly shared) fans: the highest speed of the shared
        activity and the rooms' temperature control; off when none wants them.

        force_off: the activity that switched them on has ended, so they go off
        even if we do not remember setting them (e.g. set by another room).
        """
        fans = self._fans() if fans is None else fans
        if not fans or smoke_active(self.hass):
            return  # smoke: fans stay off
        key = fan_key(fans)
        act = fan_activities(self.hass).get(key)
        speeds = [act.pct] if act is not None and act.pct is not None else []
        speeds += [
            r._fan_temp_pct for r in self._fan_rooms()
            if r._fan_temp_pct is not None and set(r._fans()) & set(fans)
        ]
        applied: dict[FanKey, int] = self.hass.data[DOMAIN].setdefault("fan_applied", {})
        if speeds:
            target = max(speeds)
            if applied.get(key) == target:
                return
            applied[key] = target
            _LOGGER.debug("%s: fans %s to %s%%", self.entity_id, fans, target)
            call = ("set_percentage", {ATTR_ENTITY_ID: fans, "percentage": target})
        else:
            was_applied = applied.pop(key, None) is not None
            if not force_off and (not was_applied or self._manual):
                return
            _LOGGER.debug("%s: fans %s off", self.entity_id, fans)
            call = ("turn_off", {ATTR_ENTITY_ID: fans})
        self.hass.async_create_task(self.hass.services.async_call("fan", call[0], call[1], blocking=True))

    @callback
    def _fan_stop_activity(self) -> None:
        """No (more) activity control: stop it, and the fans if it had started them."""
        key = fan_key(self._fans())
        if key is not None and key in fan_activities(self.hass):
            self._fan_end_activity(key)
            self._fan_notify()

    def _motion_block_reason(self) -> str | None:
        """Why motion would not switch the lights on now (None = it would)."""
        if self._manual:
            return "manual"
        if not self._members:
            return "no_lights"
        if self._armed_home_no_motion():
            return "armed_home_no_motion"
        motion_lamps = self._motion_lamps()
        if not motion_lamps:
            return "no_motion_lamps"
        if not presence_allows(self.hass, self._room) and self._alarm_mode() != "home":
            return "nobody_home"
        allowed = [e for e in motion_lamps if self._motion_ok(e)]
        if not allowed:
            if self._alarm_mode() == "away":
                return "armed_away"
            if self._evening_lamps():
                return "slot"
            if self._lux_lamps_now():
                return "lux_control"
            return "too_bright"  # sun up and lighter than "dark from"
        if all((st := self.hass.states.get(e)) is not None and st.state == STATE_ON for e in allowed):
            return "already_on"
        return None

    @callback
    def _check_idle(self) -> None:
        """Start the no-motion timer when lights are on without motion; else stop it.

        Applies to lights motion (or the door) switched on.
        """
        hold = self._last_motion_hold_left()
        idle_lamps = bool(self._idle_lamps())
        idle = (
            not self._manual and not self._any_motion() and idle_lamps
            and hold <= 0 and not self._media_active()
        )
        if self._cancel_hold:
            self._cancel_hold()
            self._cancel_hold = None
        if hold > 0 and idle_lamps and not self._manual:
            # The last motion in the house was here: check again when that hold ends.
            self._cancel_hold = async_call_later(self.hass, hold + 1, self._hold_expired)
        if not idle:
            if self._cancel_motion_off:
                self._cancel_motion_off()
                self._cancel_motion_off = None
                self._set_grace(None)
        elif self._cancel_motion_off is None:
            delay = self._motion_off_delay()
            if self._restored_grace is not None:
                # The grace period that ran before a restart: only what was left of it.
                left = (self._restored_grace - dt_util.utcnow()).total_seconds()
                self._restored_grace = None
                delay = int(min(delay, max(1, left)))
            self._cancel_motion_off = async_call_later(self.hass, delay, self._motion_timeout)
            self._set_grace(dt_util.utcnow() + timedelta(seconds=delay))

    def _idle_lamps(self) -> list[str]:
        """Lamps that are on and should go off after the grace period without motion:
        those motion or the door switched on, and (armed home, motion only) all of them."""
        on = [e for e in self._members if (st := self.hass.states.get(e)) is not None and st.state == STATE_ON]
        if not on:
            return []
        if self._armed_home_no_motion():
            return []  # armed home, not on motion: what is on (clock, by hand) stays on
        if self._alarm_mode() == "home":
            return on  # armed home: everything follows motion
        held = set(self._evening_lamps()) | set(self._lux_lamps_now())  # a time slot holds these
        lamps: set[str] = set()
        if self._on_by_motion:
            lamps |= set(self._motion_lamps()) | set(self._door_lamps())
        return [e for e in on if e in lamps and e not in held]

    def _fan_run_on(self) -> int:
        """Seconds the fan keeps running after the last motion (default: the grace period)."""
        value = self._room.get(CONF_FAN_RUN_ON)
        if not isinstance(value, (int, float)):
            return self._motion_off_delay()
        return int(min(FAN_RUN_ON_MAX, max(0, value)))

    def _motion_off_delay(self) -> int:
        """Grace period in seconds: the room's setting (0-10 min) or the default."""
        value = self._room.get(CONF_MOTION_OFF_DELAY)
        base = MOTION_OFF_DELAY if not isinstance(value, (int, float)) else int(min(MOTION_OFF_DELAY_MAX, max(0, value)))
        if self._room.get(CONF_ADAPTIVE_GRACE) and (learn := self._learn()) is not None:
            return base + learn.grace_extra(self._area_id)
        return base

    @callback
    def _set_grace(self, until: datetime | None) -> None:
        if until == self._grace_until:
            return
        self._grace_until = until
        if self.hass is not None and self.entity_id:
            self._recompute()
            self.async_write_ha_state()

    @callback
    def _motion_timeout(self, _now: Any) -> None:
        self._cancel_motion_off = None
        self._set_grace(None)
        if not self._any_motion() and (lamps := self._idle_lamps()):
            self._auto_off("no motion", lamps=lamps)
            if not self._manual and not self._late_home_holds():
                self._idle_off_at = dt_util.utcnow()

    @callback
    def _on_sun_change(self, event: Event) -> None:
        self._evaluate_covers()
        own = self._evaluate_own_times()  # slots that start at schemer/donker or end at sunrise
        if not self._evaluate_conditions() and not own:
            self._dusk_ramp()  # schemer: a bit brighter as the sun sinks
        if self._late_home_holds():
            self._on_late_home()  # sunset while someone comes home later: bundles on
        self._recompute()
        self._check_idle()
        self.async_write_ha_state()

    @staticmethod
    def _settled(state: State | None) -> str | None:
        if state is None or state.state in ALARM_TRANSITIONAL:
            return None
        return state.state

    @callback
    def _on_alarm_change(self, event: Event) -> None:
        new = self._settled(event.data.get("new_state"))
        if new is None:
            return  # arming/pending/unavailable: wait for the settled state
        previous, self._alarm_settled = self._alarm_settled, new
        if previous is None and self._alarm_started:
            # The alarm panel only now became available: apply its state.
            self._apply_alarm_state(new)
            self._reconcile_alarm_dim()
            self._recompute()
            self._check_idle()
            self.async_write_ha_state()
            return
        entered = previous is not None and previous != new
        if entered and not self._manual:
            if new == ALARM_ARMED_HOME:
                # Off, unless someone is still moving: then it stays on (at Dim)
                # and goes off after the grace period without motion. Not on
                # motion (room option): always off.
                if self._any_motion() and not self._armed_home_no_motion():
                    self._on_by_motion = True
                else:
                    if self.is_on:
                        self._alarm_last_off = dt_util.utcnow()
                    self._auto_off("alarm armed home")
            elif new == ALARM_ARMED_AWAY:
                if lamps := sorted(self._alarm_blocked()):
                    if self.is_on:
                        self._alarm_last_off = dt_util.utcnow()
                    self._auto_off("alarm armed away", lamps=lamps)
            elif previous in (ALARM_ARMED_HOME, ALARM_ARMED_AWAY):
                # Back to normal: if a time slot wants light now, give it.
                if lamps := self._evening_lamps():
                    self._auto_on("alarm off, time slot, sun down", lamps=lamps)
                elif self._lux_lamps_now():
                    self._regulate_lux(force=True)
        # Dim at armed home.
        if entered or previous is None:
            self._reconcile_alarm_dim()
        # The motion-only rule starts or stops with the alarm state.
        self._recompute()
        self._check_idle()
        self.async_write_ha_state()

    @callback
    def _alarm_startup(self, _hass: Any = None) -> None:
        """Home Assistant has started: check the alarm's state and apply it, as
        if it had just gone there (armed home: lamps off unless someone is
        moving, Dim; armed away: the blocked lamps off)."""
        self._alarm_started = True
        alarm = self._alarm_entity() if self._members else None
        state = self._settled(self.hass.states.get(alarm)) if alarm else None
        self._alarm_settled = state
        if state is None:
            return  # unknown yet: _on_alarm_change applies it when it is known
        self._apply_alarm_state(state)
        self._reconcile_alarm_dim()
        self._recompute()
        self._check_idle()
        self.async_write_ha_state()

    @callback
    def _apply_alarm_state(self, state: str) -> None:
        """What an armed state means for the lamps that are on now."""
        if self._manual:
            return
        if state == ALARM_ARMED_HOME:
            if self.is_on and not (self._any_motion() and not self._armed_home_no_motion()):
                self._alarm_last_off = dt_util.utcnow()
                self._auto_off("alarm armed home (startup)")
            elif self._any_motion() and not self._armed_home_no_motion():
                self._on_by_motion = True
        elif state == ALARM_ARMED_AWAY:
            on = {e for e in self._members if (st := self.hass.states.get(e)) is not None and st.state == STATE_ON}
            if lamps := sorted(self._alarm_blocked() & on):
                self._alarm_last_off = dt_util.utcnow()
                self._auto_off("alarm armed away (startup)", lamps=lamps)

    def _alarm_state(self) -> str | None:
        alarm = self._alarm_entity()
        state = self.hass.states.get(alarm) if alarm else None
        return state.state if state is not None else None

    def _armed_home_motion_only(self) -> bool:
        """Armed home: nothing but motion switches the lamps on (dusk, time slots,
        door, lux control don't); in "no_motion" mode motion doesn't either."""
        return self._alarm_mode() == "home"

    def _armed_home_no_motion(self) -> bool:
        """Armed home and the room chose "no_motion": the lamps don't react to
        motion; the alarm clock and switching on by hand still work."""
        return self._alarm_mode() == "home" and self._room.get(CONF_ARMED_HOME_MODE) == ARMED_HOME_NO_MOTION

    def _settings(self) -> dict[str, Any]:
        return self.hass.data.get(DOMAIN, {}).get("settings", {})

    def _alarm_entity(self) -> str | None:
        """The room's own alarm panel, or else the one from the general settings."""
        return self._room.get(CONF_ALARM_ENTITY) or self._settings().get(SETTING_ALARM_ENTITY) or None

    def _alarm_dim_for(self, state: str | None) -> bool:
        """Armed home (on motion): the lamps burn at Dim."""
        return state == ALARM_ARMED_HOME and self._room.get(CONF_ARMED_HOME_MODE) != ARMED_HOME_NO_MOTION

    @callback
    def _reconcile_alarm_dim(self) -> None:
        """1% mode on while armed home (if enabled); off again when it ends,
        but only if the alarm switched it on (a manual 1% is left alone)."""
        if self._manual or not self._members:
            return
        state = self._alarm_state() if self._alarm_entity() else None
        wanted = state is not None and self._alarm_dim_for(state)
        if wanted and not self.dimmed:
            self._dim_by_alarm = True
            self.hass.async_create_task(self.async_set_dim(True, by_alarm=True))
        elif not wanted and self.dimmed and self._dim_by_alarm:
            self._dim_by_alarm = False
            self.hass.async_create_task(self.async_set_dim(False, by_alarm=True))

    # ── lifecycle ──────────────────────────────────────────────────────────

    # ── for lamp group lights ──────────────────────────────────────────────

    @property
    def manual_active(self) -> bool:
        return self._manual

    @property
    def room_config(self) -> dict[str, Any]:
        return self._room

    async def async_call_lamps(self, service: str, lamps: list[str], **data: Any) -> None:
        """Switch some of the room's lamps, with fixed levels and daylight colour."""
        await self._async_call(service, lamps=lamps, **data)

    # ── manual control ─────────────────────────────────────────────────────

    @property
    def _manual(self) -> bool:
        # Smoke: RoomControl does nothing automatic until "Alles veilig".
        return self._manual_until is not None or smoke_active(self.hass)

    def _manual_duration(self) -> int:
        """Minutes of manual control: the room's setting (5 min - 8 h) or 60."""
        value = self._room.get(CONF_MANUAL_DURATION)
        if not isinstance(value, (int, float)):
            return MANUAL_DURATION_DEFAULT
        return int(min(MANUAL_DURATION_MAX, max(MANUAL_DURATION_MIN, value)))

    @callback
    def async_set_manual(self, minutes: float | None) -> None:
        """Start manual control (minutes; None = the room's duration) or stop it (0)."""
        if self._cancel_manual:
            self._cancel_manual()
            self._cancel_manual = None
        if minutes == 0:
            self._end_manual()
            return
        seconds = (minutes if minutes is not None else self._manual_duration()) * 60
        self._manual_until = dt_util.utcnow() + timedelta(seconds=seconds)
        self._dbg("info", "manual_start", minutes=round(seconds / 60))
        self._cancel_manual = async_call_later(self.hass, seconds, self._manual_expired)
        self._check_idle()  # stops a running grace period
        self._recompute()
        self.async_write_ha_state()

    @callback
    def _manual_expired(self, _now: Any) -> None:
        self._cancel_manual = None
        self._end_manual()

    @callback
    def _end_manual(self) -> None:
        """RoomControl takes over again and applies the rules to the current state."""
        if self._manual_until is None:
            return
        self._manual_until = None
        self._dbg("info", "manual_end")
        room = self._room
        motion_keeps = self._any_motion() and presence_allows(self.hass, room)
        on = [e for e in self._members if (st := self.hass.states.get(e)) is not None and st.state == STATE_ON]
        not_allowed = [e for e in on if e not in self.lamps_allowed([e])]
        if not_allowed and not motion_keeps:
            self._auto_off("manual control ended: lights not allowed now", lamps=not_allowed)
        elif not self.is_on and self._any_motion(switching=True) and self._is_dark() and presence_allows(self.hass, room):
            self._on_by_motion = True
            self._auto_on("manual control ended: motion", by_motion=True, lamps=self._motion_lamps())
        elif self.is_on and motion_keeps:
            self._on_by_motion = True
        self._check_idle()
        self._last_kelvins = {}
        self._daylight_tick()
        self._recompute()
        self.async_write_ha_state()

    @property
    def dimmed(self) -> bool:
        """The room's own 1% mode (button / alarm), shown on the 1% button."""
        return self._dim_room

    def _dimmed_lamps(self) -> set[str]:
        lamps = set(self._dim_slots)
        if self._dim_room:
            lamps |= {e for e in self._members if self._bopt(e, "dim", True)}
        # An alarm clock going off (or snoozing) sets its bundles' brightness
        # itself: Dim is paused for them until the clock is over.
        return (lamps & set(self._members)) - self._clock_lamps()

    def _clock_lamps(self) -> set[str]:
        clocks = self.hass.data.get(DOMAIN, {}).get("clocks") if self.hass else None
        return clocks.lamps_ringing(self._area_id) if clocks is not None else set()

    @callback
    def _on_clocks_updated(self, *_: Any) -> None:
        """A clock started, snoozed or ended: lamps whose clock is over and that
        should be on Dim (and are on) go to the Dim level now."""
        ringing = self._clock_lamps()
        ended, self._clock_prev = self._clock_prev - ringing, ringing
        if ended and (back := ended & self._dimmed_lamps()):
            self.hass.async_create_task(self._async_apply_dim(set(), back))
        self.refresh_state()

    def _lamp_dimmed(self, entity_id: str) -> bool:
        return entity_id in self._dimmed_lamps()

    async def _async_apply_dim(self, before: set[str], after: set[str]) -> None:
        """Lamps entering 1% mode go to 1% (if on); lamps leaving it get their
        remembered brightness back (if on; 100% if unknown). Off stays off."""
        def is_on(e: str) -> bool:
            return (st := self.hass.states.get(e)) is not None and st.state == STATE_ON

        entering = [e for e in self._members if e in after and e not in before]
        leaving = [e for e in self._members if e in before and e not in after]
        to_dim: dict[int, list[str]] = {}
        for e in entering:
            if is_on(e):
                b = self.hass.states.get(e).attributes.get(ATTR_BRIGHTNESS)
                self._dim_saved.setdefault(e, int(b) if isinstance(b, (int, float)) else 255)
                to_dim.setdefault(self._dim_pct(e), []).append(e)
        for pct, ids in to_dim.items():
            await rc_call(self.hass,
                "light", "turn_on", {ATTR_ENTITY_ID: ids, "brightness_pct": pct}, blocking=True
            )
        for e in leaving:
            brightness = self._dim_saved.pop(e, 255)
            if is_on(e):
                await rc_call(self.hass,
                    "light", "turn_on", {ATTR_ENTITY_ID: e, ATTR_BRIGHTNESS: brightness}, blocking=True
                )

    @property
    def follows_dim(self) -> bool:
        """At least one lamp takes part in Dim (bundle option "Doet mee met Dim");
        "Alles dim" leaves rooms without one alone."""
        return any(self._bopt(e, "dim", True) for e in self._members)

    async def async_set_dim(self, dim: bool, by_alarm: bool = False) -> None:
        """Room 1% mode on (lamps that are on go to 1%, off stays off) or off.

        While the mode is on, any lamp that goes on burns at 1%. Each lamp's
        brightness from before (or the one it was switched on with during the
        mode) is remembered and restored when the mode ends.
        """
        if not by_alarm:
            self._dim_by_alarm = False  # the user decides now; leaving armed home won't undo it
        if dim == self._dim_room or not self._members:
            return
        before = self._dimmed_lamps()
        self._dim_room = dim
        after = self._dimmed_lamps()
        self._recompute()
        self.async_write_ha_state()
        await self._async_apply_dim(before, after)

    def _dim_remember(self, entity_id: str, brightness: int) -> None:
        """A lamp in 1% mode: remember what it would have burned at."""
        if self._lamp_dimmed(entity_id):
            self._dim_saved[entity_id] = int(min(255, max(1, brightness)))

    # ── memory across a restart ────────────────────────────────────────────

    def _memory_key(self) -> str:
        return f"room:{self._area_id}"

    def _memory_data(self) -> dict[str, Any]:
        """What this room keeps across a restart (see memory.py)."""
        iso = lambda t: t.isoformat() if t else None  # noqa: E731
        return {
            "dim_room": self._dim_room,
            "dim_by_alarm": self._dim_by_alarm,
            "dim_saved": dict(self._dim_saved),
            "manual_until": iso(self._manual_until),
            "late_pending": self._late_pending,
            "late_on_done": self._late_on_done,
            "on_by_motion": self._on_by_motion,
            "grace_until": iso(self._grace_until),
            "hand_set": sorted(self._hand_set),
            "replay_on": sorted(self._replay_on),
            "alarm_last_off": iso(self._alarm_last_off),
            "idle_off_at": iso(self._idle_off_at),
            "last_motion_at": iso(self._last_motion_at),
            "debug": list(self._debug),
        }

    @callback
    def _restore_memory(self) -> None:
        """Put the room back as it was before the restart: Dim (with the
        brightness to return to), manual control until its end time, the
        grace period, Home later, lamps set by hand and the debug log."""
        mem = self.hass.data.get(DOMAIN, {}).get("memory")
        data = mem.get(self._memory_key()) if mem else None
        if mem:
            self.async_on_remove(mem.register(self._memory_key(), self._memory_data))
        if not isinstance(data, dict):
            return
        when = lambda k: dt_util.parse_datetime(data[k]) if isinstance(data.get(k), str) else None  # noqa: E731
        now = dt_util.utcnow()
        self._dim_room = bool(data.get("dim_room"))
        self._dim_by_alarm = bool(data.get("dim_by_alarm")) and self._dim_room
        self._dim_saved = {
            k: int(v) for k, v in (data.get("dim_saved") or {}).items() if isinstance(v, (int, float))
        }
        if (until := when("manual_until")) is not None and until > now:
            self._manual_until = until
            self._cancel_manual = async_call_later(self.hass, (until - now).total_seconds(), self._manual_expired)
        self._late_pending = bool(data.get("late_pending"))
        self._late_on_done = bool(data.get("late_on_done"))
        self._on_by_motion = bool(data.get("on_by_motion"))
        self._restored_grace = when("grace_until")
        self._hand_set = {e for e in data.get("hand_set") or [] if isinstance(e, str)}
        self._replay_on = {e for e in data.get("replay_on") or [] if isinstance(e, str)}
        self._alarm_last_off = when("alarm_last_off")
        self._idle_off_at = when("idle_off_at")
        self._last_motion_at = when("last_motion_at") or self._last_motion_at
        for entry in data.get("debug") or []:
            if isinstance(entry, dict):
                self._debug.append(entry)
        self._dbg("info", "restart")

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN].setdefault("entities", {})[self._area_id] = self
        self._restore_memory()
        self._subscribe()
        self._prev_motion_lamps = set(self._motion_lamps())
        self._prev_dim_lamps = self._dim_bundle_lamps()
        self._check_idle()  # e.g. lights already on without motion at startup
        self.async_on_remove(async_at_started(self.hass, self._alarm_startup))
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._on_config_updated)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_LATE_HOME, self._on_late_home)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_VACATION, self._on_vacation)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_LAST_MOTION, self._on_last_motion)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_SMOKE, self.refresh_state)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_CLOCKS_UPDATED, self._on_clocks_updated)
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_VACUUM_UPDATED, self._on_vacuum_updated)
        )

    @callback
    def _on_vacation(self) -> None:
        """Vacation on/off: other time slots may run now."""
        self._evaluate_own_times()
        self._recompute()
        self.async_write_ha_state()

    def _vacuum_attrs(self) -> dict[str, Any]:
        """When the room was last vacuumed and what its cleaning moments do (panel)."""
        manager = self.hass.data.get(DOMAIN, {}).get("vacuums")
        if manager is None:
            return {}
        return {
            "vacuumed_at": manager.last_clean.get(self._area_id),
            "vacuum_plans": manager.plan_info(self._area_id),
        }

    @callback
    def _on_vacuum_updated(self) -> None:
        self._recompute()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        if entities.get(self._area_id) is self:
            del entities[self._area_id]
        for _ids, unsub in self._tracks.values():
            unsub()
        self._tracks.clear()
        if self._cancel_motion_off:
            self._cancel_motion_off()
            self._cancel_motion_off = None
        if self._cancel_daylight:
            self._cancel_daylight()
            self._cancel_daylight = None
        if self._cancel_lux_interval:
            self._cancel_lux_interval()
            self._cancel_lux_interval = None
        if self._cancel_evening_check:
            self._cancel_evening_check()
            self._cancel_evening_check = None
        if self._cancel_manual:
            self._cancel_manual()
            self._cancel_manual = None
        if self._cancel_hold:
            self._cancel_hold()
            self._cancel_hold = None
        if self._cancel_smart_tick:
            self._cancel_smart_tick()
            self._cancel_smart_tick = None
        if self._cancel_cover_time:
            self._cancel_cover_time()
            self._cancel_cover_time = None
        for cancel in self._bright_pending.values():
            cancel()
        self._bright_pending.clear()
        # Last room using these fans gone (e.g. reload): drop the activity's timers.
        if (key := fan_key(self._fans())) and not [r for r in self._fan_rooms() if r is not self]:
            if (act := fan_activities(self.hass).pop(key, None)) is not None:
                act.cancel_all()
                if act.pct is not None and not self.hass.is_stopping:
                    self._fan_apply(list(key), force_off=True)  # we switched them on

    # ── commands ───────────────────────────────────────────────────────────

    async def _async_call(
        self, service: str, lamps: list[str] | None = None, levels: dict[str, int] | None = None, **data: Any
    ) -> None:
        """Call a light service for the room's lamps (or just `lamps`)."""
        targets = self._members if lamps is None else [e for e in self._members if e in lamps]
        if not targets:
            return
        if service != "turn_on":
            await rc_call(self.hass,
                "light", service, {ATTR_ENTITY_ID: targets, **data}, blocking=True
            )
            return
        # Per lamp: daylight colour if it follows the sun, its fixed level if it
        # is pinned (ignoring any requested brightness), else the request.
        colour = set(self._daylight_members())
        fixed = self._fixed_levels()
        groups: dict[tuple[tuple[str, Any], ...], list[str]] = {}
        off: list[str] = []
        for entity_id in targets:
            extra: dict[str, Any] = {}
            modes = _lamp_modes(self.hass, entity_id)
            if ATTR_HS_COLOR in data and modes & RGB_COLOR_MODES:
                extra[ATTR_HS_COLOR] = tuple(data[ATTR_HS_COLOR])  # colour chosen on the RoomControl light
            elif ATTR_COLOR_TEMP_KELVIN in data and modes & KELVIN_COLOR_MODES:
                extra.update(self._colour_data(entity_id, int(data[ATTR_COLOR_TEMP_KELVIN])))
            elif entity_id in colour and (kelvin := self._kelvin_for(entity_id)) is not None:
                extra.update(self._colour_data(entity_id, kelvin))
            if levels and entity_id in levels:
                extra["brightness_pct"] = levels[entity_id]  # schemer ramp / donker level
            elif entity_id in fixed:
                extra["brightness_pct"] = fixed[entity_id]
            elif ATTR_BRIGHTNESS in data:
                extra[ATTR_BRIGHTNESS] = data[ATTR_BRIGHTNESS]
            elif (default := self._default_pct_for(entity_id)) and not (
                (st := self.hass.states.get(entity_id)) is not None and st.state == STATE_ON
            ):
                extra["brightness_pct"] = default  # standard brightness for a lamp going on
            if self._lamp_dimmed(entity_id):
                # 1% mode: burn at 1%, remember what it would have been.
                was_on = (st := self.hass.states.get(entity_id)) is not None and st.state == STATE_ON
                if not was_on:
                    intended = (
                        round(extra["brightness_pct"] * 255 / 100) if "brightness_pct" in extra
                        else extra.get(ATTR_BRIGHTNESS, 255)
                    )
                    self._dim_remember(entity_id, intended)
                extra.pop(ATTR_BRIGHTNESS, None)
                extra["brightness_pct"] = self._dim_pct(entity_id)
            if _reads_zero(extra):
                off.append(entity_id)  # 0%: off, not on at a level nobody can see
                continue
            groups.setdefault(tuple(sorted(extra.items())), []).append(entity_id)
        if off:
            await rc_call(self.hass, "light", "turn_off", {ATTR_ENTITY_ID: off}, blocking=True)
        for extra_items, ids in groups.items():
            await rc_call(self.hass,
                "light", "turn_on", {ATTR_ENTITY_ID: ids, **dict(extra_items)}, blocking=True
            )

    async def async_turn_on(self, **kwargs: Any) -> None:
        lamps = self.lamps_allowed(list(self._members))
        if self._members and not lamps:
            raise HomeAssistantError(
                f"{self.name or self.entity_id}: lights are blocked (nobody home)"
            )
        data = {ATTR_BRIGHTNESS: kwargs[ATTR_BRIGHTNESS]} if ATTR_BRIGHTNESS in kwargs else {}
        await self._async_call("turn_on", lamps=lamps, **data, **_colour_request(kwargs))

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._on_by_motion = False
        await self._async_call("turn_off")
        # All off: the room's switches that go off with it.
        from .room_switches import async_switch_off, switches_for  # here: avoids an import cycle

        await async_switch_off(self.hass, switches_for(self.hass, "all_off", self._area_id), "all off")
