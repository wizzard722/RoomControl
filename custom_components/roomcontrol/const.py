"""Constants for RoomControl."""
from __future__ import annotations

from typing import Any

DOMAIN = "roomcontrol"
TITLE = "RoomControl"
# Must match manifest.json "version" and the panel's EXPECTED_BACKEND_VERSION;
# the panel warns when they differ (e.g. HA not restarted after an update).
VERSION = "3.0.4"

# Only used by version-1 config entries (one entry per area), for migration.
CONF_AREA_ID = "area_id"

STORAGE_KEY = DOMAIN
# Storage key of the integration's previous name (LightRoom). Rooms saved
# there are copied once into STORAGE_KEY when RoomControl has none yet.
LEGACY_STORAGE_KEY = "lightroom"
STORAGE_VERSION = 1

# Fired (via the dispatcher) whenever rooms config or area membership changes.
SIGNAL_CONFIG_UPDATED = f"{DOMAIN}_config_updated"

# Room option: turn the room's lights off when the alarm goes
# from disarmed to armed_home.
CONF_OFF_ON_ARMED_HOME = "turn_off_on_armed_home"
# Room option: while the alarm is armed_home,
# lights react to motion only: they go off after the grace period without
# motion (however they were switched on) and dusk/door switch nothing on.
CONF_ARMED_HOME_MOTION_ONLY = "armed_home_motion_only"
# Room option: what the lamps do while the alarm is armed_home.
# "motion" (default): off, except where there is motion; motion switches on
#   at Dim, off after the grace period.
# "no_motion": off, and motion/door switch nothing on; the alarm clock and
#   switching on by hand still work, and those lamps stay on.
CONF_ARMED_HOME_MODE = "armed_home_mode"
ARMED_HOME_MOTION = "motion"
ARMED_HOME_NO_MOTION = "no_motion"
# Room option (with "no_motion"): at armed home the lamps that are on go to
# Dim instead of off, and every lamp switched on burns at Dim; motion still
# switches nothing on. Lamps of an alarm clock keep their own level.
CONF_ARMED_HOME_DIM = "armed_home_dim"
CONF_ALARM_ENTITY = "alarm_entity"

# Room option: person.* entities; lights are only allowed while at least one
# of them is home (only persons enabled in the global settings count).
CONF_PERSONS = "persons"
# Global settings
SETTING_PERSONS = "persons"
SETTING_GROUP_BY_FLOOR = "group_by_floor"
# Alarm panel for the whole house (rooms without their own use this one)
SETTING_ALARM_ENTITY = "alarm_entity"
# 1% mode while the alarm is armed_home, for all rooms (rooms can override)
SETTING_DIM_ON_ARMED_HOME = "dim_on_armed_home"
# Sun entity for the whole house: decides whether the sun is down.
SETTING_SUN_ENTITY = "sun_entity"
# Schemer (dusk) starts when the sun is lower than this many degrees above the
# horizon; donker (dark) starts when it sets. So the day has three phases:
# licht → schemer → donker.
SETTING_DUSK_ELEVATION = "dusk_elevation"
DUSK_ELEVATION_DEFAULT = 5.0
# Bundles on from schemer (a time slot that starts at schemer) go from 0% up to
# their own level while the sun sinks (at sunset: their own level).
# Brightness % of Dim for the whole house (Dim button, Dim at armed home, a
# time slot's "Dim vanaf" without its own level). Default 1%.
SETTING_DIM_LEVEL = "dim_level"
DIM_LEVEL_DEFAULT = 1
# Room option: following curtains close at "dark" (default) or already at "dusk".
CONF_COVERS_CLOSE_AT = "covers_close_at"
# When following curtains open in the morning: "light" (sunrise, per the Sun
# integration) or "time" (CONF_COVERS_OPEN_TIME, "HH:MM"); unset = as before
# (never automatically).
CONF_COVERS_OPEN_AT = "covers_open_at"
CONF_COVERS_OPEN_TIME = "covers_open_time"
# Persons that get a "Later thuis" (home later) switch on the General device.
SETTING_LATE_HOME_PERSONS = "late_home_persons"
# Room option: while a "Later thuis" switch is on, the room's bundles don't go off.
CONF_LATE_HOME = "late_home"
# Fired when a "Later thuis" switch goes on or off.
SIGNAL_LATE_HOME = "roomcontrol_late_home"
# Fired when the "Vakantie" switch (General device) goes on or off. Time slots
# of bundles can be for vacation only, or not during vacation.
SIGNAL_VACATION = "roomcontrol_vacation"
# The room with the last motion in the house changed.
SIGNAL_LAST_MOTION = "roomcontrol_last_motion"
# Setting: the vacation mode follows the alarm panel (general settings): on
# while it is "armed_vacation", off when it leaves that state.
# Identifier of the General device (house-wide entities).
GENERAL_DEVICE = "general"
DEFAULT_SETTINGS = {
    SETTING_PERSONS: [],
    SETTING_GROUP_BY_FLOOR: False,
    SETTING_ALARM_ENTITY: "",
    SETTING_DIM_ON_ARMED_HOME: False,
    SETTING_SUN_ENTITY: "sun.sun",
    SETTING_DUSK_ELEVATION: DUSK_ELEVATION_DEFAULT,
    SETTING_DIM_LEVEL: DIM_LEVEL_DEFAULT,
    "late_home_persons": [],
}
# Room override of SETTING_DIM_ON_ARMED_HOME: "default" (follow), "on", "off"
CONF_DIM_ON_ARMED_HOME = "dim_on_armed_home"

# Room option: colour temperature follows the sun (warm low, cool high).
CONF_FOLLOW_DAYLIGHT = "follow_daylight"
# Lamps that follow the sun (subset of the room's lights). Missing = all
# capable lamps (older rooms); empty list = none.
CONF_DAYLIGHT_LIGHTS = "daylight_lights"
# Daylight colour options (after Adaptive Lighting):
# - prefer RGB: lamps that can do colour get the sun's colour as rgb_color
#   (like Adaptive Lighting's prefer_rgb_color); others get color_temp_kelvin
#   within their own min/max range;
# - warmest / coolest colour temperature of the room (defaults 2200 / 5000 K).
CONF_DAYLIGHT_PREFER_RGB = "daylight_prefer_rgb"
CONF_DAYLIGHT_MIN_KELVIN = "daylight_min_kelvin"
CONF_DAYLIGHT_MAX_KELVIN = "daylight_max_kelvin"
RGB_COLOR_MODES = {"hs", "xy", "rgb", "rgbw", "rgbww"}
DAYLIGHT_MIN_KELVIN = 2200  # sun at/below DAYLIGHT_LOW_ELEVATION
DAYLIGHT_MAX_KELVIN = 5000  # sun at/above DAYLIGHT_HIGH_ELEVATION
DAYLIGHT_LOW_ELEVATION = -6.0  # civil dusk
DAYLIGHT_HIGH_ELEVATION = 40.0
DAYLIGHT_UPDATE_INTERVAL = 300  # seconds
# Colour modes that accept color_temp_kelvin
KELVIN_COLOR_MODES = {"color_temp", "hs", "xy", "rgb", "rgbw", "rgbww"}

# Room option: one or more motion sensors (any on = motion). The single
# `motion_sensor` key is the older format and is still read.
CONF_MOTION_SENSORS = "motion_sensors"
# Per motion sensor a time window {"start": "HH:MM", "end": "HH:MM"} in which it
# may switch the lights on; no window = always. A window may run past midnight.
CONF_MOTION_WINDOWS = "motion_windows"
# Room option: linked rooms (area_ids). Links work both ways and chain: the
# rooms form a group that shares motion (any sensor in the group = motion).
CONF_LINKED_ROOMS = "linked_rooms"
CONF_MOTION_SENSOR = "motion_sensor"
CONF_TURN_ON_AT_DUSK = "turn_on_at_dusk"
CONF_SUN_ENTITY = "sun_entity"
CONF_LUX_SENSOR = "lux_sensor"
# Room option: one or more lux sensors, combined with lux_mode into one value.
# The single `lux_sensor` key is the older format and is still read.
CONF_LUX_SENSORS = "lux_sensors"
CONF_LUX_MODE = "lux_mode"
LUX_MODES = ("average", "min", "max", "median", "sum")
DEFAULT_LUX_MODE = "average"
CONF_TARGET_LUX = "target_lux"
# Lux, option 1: below this many lux the room counts as dark (motion and the
# door sensor only switch on when dark). Missing → target_lux (older rooms).
CONF_DARK_LUX = "dark_lux"
# Lux, option 2: while it is light outside (sun up), keep adjusting the lamps
# until the room reaches target_lux.
CONF_LUX_CONTROL = "lux_control"
# Room switch for option 2: the target lux can be turned off as a whole
# (missing → on, older rooms). Off = no lux control for any lamp.
CONF_TARGET_LUX_ENABLED = "target_lux_enabled"
# Room option: alarm states (e.g. ["armed_away"]) in which lux control pauses.
CONF_LUX_CONTROL_OFF_ALARM = "lux_control_off_alarm"
# Room's standard brightness (percent): lamps switched on go to this level;
# once it is dark (sun down) this is used instead of lux control.
CONF_DEFAULT_BRIGHTNESS = "default_brightness"
LUX_CONTROL_INTERVAL = 60  # s, regular check besides every lux reading
LUX_CONTROL_MIN_GAP = 30  # s between two adjustments (let the sensor settle)
LUX_CONTROL_DEADBAND = 0.10  # within ±10% of the target: leave it
LUX_CONTROL_MAX_STEP = 0.25  # change brightness by at most 25% per step
LUX_CONTROL_START_PCT = 30  # lamps switched on by lux control start here
LUX_CONTROL_MIN_BRIGHTNESS = 3  # of 255 (= 1%, the lowest level): still too light there → off
# Room option: ignore armed_away here — the room keeps following its time
# slots (and goes off when a slot ends). Older rooms may have it per bundle.
CONF_AWAY_FOLLOW_SCHEDULE = "away_follow_schedule"
# Room option: the room's media players (media_player.*), shown in the panel.
# For now they don't change any rule (lamps, time slots, alarm).
CONF_MEDIA_PLAYERS = "media_players"

# Smart room options (all off unless switched on in the panel).
# Grace period learns: longer when lights go off too early, shorter otherwise.
CONF_ADAPTIVE_GRACE = "adaptive_grace"
# A media player of the room that plays keeps the lights on (no grace period).
CONF_MEDIA_HOLD = "media_hold"
# Media player states that count as "in use".
MEDIA_ACTIVE_STATES = ("playing", "paused", "on", "buffering")
# The last motion in the house was here: someone is probably still here, the
# lights stay on (at most LAST_MOTION_HOLD_MAX) until motion elsewhere.
CONF_LAST_MOTION_HOLD = "last_motion_hold"
LAST_MOTION_HOLD_MAX = 45 * 60  # s
# Learn the standard brightness per lamp and hour from changes made by hand.
CONF_LEARN_BRIGHTNESS = "learn_brightness"
# Nobody home (or armed away) and dark: replay when the lamps were on, on the
# same weekday last time, shifted a little per day.
CONF_AWAY_REPLAY = "away_replay"
# Notify on motion at an hour that never had any, and on lights left on long
# without motion.
CONF_ANOMALY_ALERTS = "anomaly_alerts"
ANOMALY_LIGHTS_ON_HOURS = 3

# Lights go off this long after motion clears ("grace period"); per room
# configurable via CONF_MOTION_OFF_DELAY between 0 and MOTION_OFF_DELAY_MAX.
MOTION_OFF_DELAY = 300  # seconds (default)
MOTION_OFF_DELAY_MAX = 600  # seconds
CONF_MOTION_OFF_DELAY = "motion_off_delay"

# Room option: door/opening sensors. With CONF_DOOR_TURN_ON, a door opening
# while the room is darker than its lux target switches on the lamps of the
# chosen lamp groups (CONF_DOOR_GROUPS, ids from CONF_GROUPS). They then go
# off after the grace period without motion, like motion-triggered light.
CONF_DOOR_SENSORS = "door_sensors"
CONF_DOOR_TURN_ON = "door_turn_on"
CONF_DOOR_GROUPS = "door_groups"
# Room option: curtains/blinds (cover.*) and named curtain groups
# [{"id", "name", "covers": [entity_id], "follow": bool}]. A group with
# "follow" closes at dusk/dark and opens per "open at" (see below).
CONF_COVERS = "covers"
# Room option: locks, [{"entity_id", "slots": [lock times: {"name", "days",
# "time": "HH:MM", "holiday", "enabled": bool (default yes)}, see locks.py], "slots_enabled": bool (default yes), "away_lock": bool, "away_minutes": int,
# "confirm_open": bool (default yes; only the panel asks)}]. RoomControl only
# ever locks by itself; opening is always a person's choice.
CONF_LOCKS = "locks"
LOCK_AWAY_MINUTES_DEFAULT = 5
CONF_COVER_GROUPS = "cover_groups"  # older rooms; the panel no longer makes these
# Room option: all of the room's curtains follow dark/light.
CONF_COVERS_FOLLOW = "covers_follow"
# Room option: curtains that run the wrong way round (open = closed), as a
# list of cover entity ids. RoomControl swaps open/close (and position
# p → 100 - p) for them, both in what it sends and in the state it shows.
CONF_COVERS_INVERTED = "covers_inverted"
# Room option: full control. The room's lamps and curtains only follow
# RoomControl (its automations, its entities and the panel); any other change is
# put back. Grace periods (s) after a RoomControl command before checking, and
# at most this many corrections per entity per minute.
CONF_FULL_CONTROL = "full_control"
FULL_CONTROL_LAMP_GRACE = 10
FULL_CONTROL_COVER_GRACE = 90
FULL_CONTROL_MAX_REVERTS = 5
# Room option: fans (fan.*) with speed steps by activity duration,
# [{"minutes": 5, "percentage": 25}, ...]. Activity starts at the first motion
# on the room's own sensors and ends after the room's grace period without
# motion; then the fans go off.
CONF_FANS = "fans"
CONF_FAN_STEPS = "fan_steps"
# Room option: rooms that share their fans (area_ids), e.g. two toilets with one
# fan. Links work both ways and chain. Every room in the group starts its own
# activity on its own motion; the shared fans run at the highest speed of the
# active rooms and only go off when none is active any more. A room without
# own fans or steps uses those of the other rooms in the group.
CONF_FAN_SHARED_ROOMS = "fan_shared_rooms"
# Room option: how long (s) the fan keeps running after the last motion before
# the activity ends and the fan goes off. Missing → the room's grace period.
CONF_FAN_RUN_ON = "fan_run_on"
FAN_RUN_ON_MAX = 3600
# Room option: fan by temperature. From fan_temp_min (°C or the sensor's unit)
# upwards the fan runs at fan_temp_speed (%), also without activity; with
# activity the highest speed counts. A small hysteresis keeps it from switching
# on and off around the limit.
CONF_FAN_TEMP_SENSOR = "fan_temp_sensor"
# Room option: the fan follows activity (motion + steps). Missing → yes.
# Off together with no temperature sensor = the fan is only operated by hand.
CONF_FAN_MOTION = "fan_motion"
CONF_FAN_TEMP_MIN = "fan_temp_min"
CONF_FAN_TEMP_SPEED = "fan_temp_speed"
FAN_TEMP_HYSTERESIS = 0.3
# Names of the room's own groups in HA (all lamps / all curtains / all fans).
# Empty: lamps use the room's name, curtains "Gordijnen", fans "Ventilator".
CONF_LIGHTS_NAME = "lights_name"
CONF_COVERS_NAME = "covers_name"
CONF_FANS_NAME = "fans_name"
DEFAULT_COVERS_NAME = "Gordijnen"
DEFAULT_FANS_NAME = "Ventilator"
# Room option: named lamp groups [{"id", "name", "lights": [entity_id]}]
CONF_GROUPS = "groups"
DOOR_OPEN_STATES = ("on", "open")

# Room option: lamps pinned to a fixed dim level, {entity_id: percent 1-100}.
# They always go on at that level and ignore brightness requests (the room's
# brightness slider, lux adaptation, brightness passed to the room light).
CONF_FIXED_LEVELS = "fixed_levels"

# Manual control: for this many minutes RoomControl does nothing automatic in
# the room; afterwards it takes over again. Per room, 5 min - 8 h.
CONF_MANUAL_DURATION = "manual_duration"
MANUAL_DURATION_DEFAULT = 60  # minutes
MANUAL_DURATION_MIN = 5
MANUAL_DURATION_MAX = 480

ALARM_DISARMED = "disarmed"
ALARM_ARMED_HOME = "armed_home"
ALARM_ARMED_AWAY = "armed_away"
# Room option: what each alarm state does in this room,
# {"disarmed" | "armed_home" | "armed_away": {"action": ..., "dim": ...}}.
# action: "none", "off" (lamps off when the state starts), "on" (lamps on when
# the state starts, if it is dark), "motion" (while in the state, lamps only
# follow motion). dim: "default" (armed_home: the general setting; other
# states: no), "on", "off". Without a rule for armed_home the older keys
# (turn_off_on_armed_home, armed_home_motion_only, dim_on_armed_home) count.
CONF_ALARM_RULES = "alarm_rules"
ALARM_RULE_STATES = (ALARM_DISARMED, ALARM_ARMED_HOME, ALARM_ARMED_AWAY)
ALARM_ACTIONS = ("none", "off", "on", "motion")
# States an alarm passes through between two settled states.
ALARM_TRANSITIONAL = {"arming", "pending", "disarming", "unavailable", "unknown"}


def energy_enabled(hass: Any) -> bool:
    """General setting "energy_enabled" (default on): off hides the energy
    management and the EV charger in the panel and pauses everything they do."""
    settings = (getattr(hass, "data", {}) or {}).get(DOMAIN, {}).get("settings", {}) or {}
    return settings.get("energy_enabled", True) is not False
