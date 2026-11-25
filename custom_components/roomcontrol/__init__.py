"""RoomControl - Home Assistant Custom Integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from .clocks import ClockManager
from .locks import LockManager
from .learn import LearnStore
from .smoke import SmokeManager
from .doorbell import DoorbellManager
from .announce import async_announce
from .nspanel import async_clear as nspanel_clear, async_show as nspanel_show, chosen_panels, found_panels, nspanel_message, stop_timers as nspanel_stop, target_panels
from .texts import default_texts
from .vacuums import VacuumManager
from .control import FullControl, rc_call
from .covers_known import CoverMemory
from .memory import Memory
from .lamp_sync import LampSync
from .room_switches import RoomSwitches, never_off
from .energy import Energy
from .tags import Tags, async_run_rule, tag_rules
from .alarm_auto import AlarmAutomation
from .entity_ids import async_prefix_entity_ids
from .rooms import all_dim_rooms
from .const import (
    CONF_AREA_ID,
    DEFAULT_SETTINGS,
    VERSION,
    DOMAIN,
    LEGACY_STORAGE_KEY,
    SIGNAL_CONFIG_UPDATED,
    STORAGE_KEY,
    STORAGE_VERSION,
    TITLE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.COVER, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.FAN, Platform.SWITCH, Platform.BUTTON, Platform.LOCK, Platform.NOTIFY]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


# ── Storage helpers ─────────────────────────────────────────────────────────


def _data(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data[DOMAIN]


async def _async_save(
    hass: HomeAssistant,
    rooms: list[dict[str, Any]] | None = None,
    settings: dict[str, Any] | None = None,
) -> None:
    """Update rooms and/or settings, persist to .storage and notify entities."""
    data = _data(hass)
    if rooms is not None:
        _without_motion(hass, data.get("rooms", []), rooms)
        data["rooms"] = rooms
    if settings is not None:
        data["settings"] = {**DEFAULT_SETTINGS, **settings}
    await data["store"].async_save({"rooms": data["rooms"], "settings": data["settings"]})
    async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED)


def _without_motion(hass: HomeAssistant, old: list[dict[str, Any]], new: list[dict[str, Any]]) -> None:
    """A room whose last motion sensor was removed: its learned grace period
    is forgotten and Smart › adaptive grace period goes off (it learns from
    motion)."""
    from .const import CONF_ADAPTIVE_GRACE  # noqa: PLC0415
    from .rooms import room_motion_sensors  # noqa: PLC0415

    before = {r.get("area_id"): bool(room_motion_sensors(r)) for r in old or [] if isinstance(r, dict)}
    for room in new:
        area = room.get("area_id") if isinstance(room, dict) else None
        if not area or not before.get(area) or room_motion_sensors(room):
            continue
        room.pop(CONF_ADAPTIVE_GRACE, None)
        if (learn := _data(hass).get("learn")) is not None:
            learn.forget(area, "grace_extra")
        _LOGGER.info("RoomControl: %s has no motion sensors any more: learned grace period forgotten", area)


def _split_both_slots(data: dict[str, Any]) -> bool:
    """Time slots for "both" (verlof and vakantie) became two slots, one for
    each (2.2.0: the choice "both" is gone). True when something changed."""
    from .slots import split_both  # noqa: PLC0415

    changed = False

    def fix(holder: dict[str, Any], key: str) -> None:
        nonlocal changed
        new, did = split_both(holder.get(key))
        if did:
            holder[key] = new
            changed = True

    for room in data.get("rooms", []):
        if not isinstance(room, dict):
            continue
        for group in room.get("groups", []) or []:
            if isinstance(group, dict):
                fix(group, "slots")
        windows = room.get("motion_windows")
        if isinstance(windows, dict):
            for sensor in list(windows):
                fix(windows, sensor)
        for lock in room.get("locks", []) or []:
            if isinstance(lock, dict):
                fix(lock, "slots")
    settings = data.get("settings", {})
    fix(settings, "all_dim_slots")
    if isinstance(settings.get("alarm"), dict):
        fix(settings["alarm"], "slots")
    return changed


async def _async_save_rooms(hass: HomeAssistant, rooms: list[dict[str, Any]]) -> None:
    await _async_save(hass, rooms=rooms)


# ── Setup ───────────────────────────────────────────────────────────────────


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Load stored rooms, register the panel and the WebSocket API."""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored = await store.async_load()
    if stored is None:
        # First start under the new name: take over rooms saved as LightRoom.
        legacy = await Store(hass, STORAGE_VERSION, LEGACY_STORAGE_KEY).async_load()
        if legacy:
            _LOGGER.info(
                "Copied %d room(s) from the old LightRoom storage", len(legacy.get("rooms", []))
            )
            await store.async_save(legacy)
        stored = legacy or {}
    hass.data[DOMAIN] = {
        "store": store,
        "rooms": list(stored.get("rooms", [])),
        "settings": {**DEFAULT_SETTINGS, **stored.get("settings", {})},
    }
    if _split_both_slots(hass.data[DOMAIN]):
        await store.async_save({"rooms": hass.data[DOMAIN]["rooms"], "settings": hass.data[DOMAIN]["settings"]})

    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_set_config)
    websocket_api.async_register_command(hass, ws_set_dim)
    websocket_api.async_register_command(hass, ws_set_manual)
    websocket_api.async_register_command(hass, ws_alarm_status)
    websocket_api.async_register_command(hass, ws_alarm_test)
    websocket_api.async_register_command(hass, ws_energy_status)
    websocket_api.async_register_command(hass, ws_devices)
    websocket_api.async_register_command(hass, ws_ev_test)
    websocket_api.async_register_command(hass, ws_solar_forecasts)
    websocket_api.async_register_command(hass, ws_nspanel)
    websocket_api.async_register_command(hass, ws_tags)

    async def _nspanel_service(call: ServiceCall) -> ServiceResponse:
        panels = await nspanel_show(
            hass, call.data.get("label") or "RoomControl", call.data["message"], call.data.get("seconds"),
            panels=target_panels(hass, call.data.get("group") or "all"))
        return {"panels": panels}

    hass.services.async_register(
        DOMAIN, "nspanel_message", _nspanel_service,
        schema=vol.Schema({
            vol.Required("message"): str,
            vol.Optional("label"): str,
            vol.Optional("seconds"): vol.Coerce(float),
            vol.Optional("group"): str,
        }),
        supports_response=SupportsResponse.OPTIONAL,
    )
    websocket_api.async_register_command(hass, ws_call_service)
    websocket_api.async_register_command(hass, ws_get_debug)
    websocket_api.async_register_command(hass, ws_plan)
    websocket_api.async_register_command(hass, ws_battery)
    websocket_api.async_register_command(hass, ws_energy_overview)
    websocket_api.async_register_command(hass, ws_energy_bill)
    websocket_api.async_register_command(hass, ws_energy_coach)
    websocket_api.async_register_command(hass, ws_battery_sim)
    websocket_api.async_register_command(hass, ws_battery_test)
    websocket_api.async_register_command(hass, ws_forget_learned)
    websocket_api.async_register_command(hass, ws_smoke_clear)
    websocket_api.async_register_command(hass, ws_restore_auto)
    websocket_api.async_register_command(hass, ws_announce)
    websocket_api.async_register_command(hass, ws_test_text)

    async def _announce_service(call: ServiceCall) -> ServiceResponse:
        areas = call.data.get("areas")
        if isinstance(areas, str):
            areas = [areas]
        players = await async_announce(hass, call.data["message"], areas or None)
        nspanel_message(hass, "announce", call.data["message"])
        return {"players": players}

    hass.services.async_register(
        DOMAIN, "announce", _announce_service,
        schema=vol.Schema({
            vol.Required("message"): str,
            vol.Optional("areas"): vol.Any(str, [str]),
        }),
        supports_response=SupportsResponse.OPTIONAL,
    )
    websocket_api.async_register_command(hass, ws_vacuum_start)

    if not os.path.isdir(FRONTEND_DIR):
        _LOGGER.error(
            "Frontend bundle not found at %s. Run `npm run build` in the frontend "
            "project; the RoomControl panel is not registered",
            FRONTEND_DIR,
        )
        return True

    # Serve the built JS bundle from custom_components/roomcontrol/frontend/
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"/{DOMAIN}/frontend", FRONTEND_DIR, cache_headers=False)]
    )

    bundle = await hass.async_add_executor_job(_bundle_version)  # file read: not in the event loop
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="roomcontrol-panel",
        frontend_url_path=DOMAIN,
        # ?v=: a new bundle gets a new URL, so the browser doesn't keep the old one.
        module_url=f"/{DOMAIN}/frontend/roomcontrol-panel.js?v={bundle}",
        sidebar_title=TITLE,
        sidebar_icon="mdi:lightbulb-group",
        require_admin=False,
    )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Version 1 had one entry per area; version 2 has one entry for all areas.

    The first old entry becomes the single entry (its light keeps the same
    unique_id, so its entity_id stays). Other old entries are removed; their
    rooms stay in storage and get a light from the single entry.
    """
    if entry.version > 1:
        return True

    # Done synchronously (no await before the update) so that concurrently
    # migrating old entries cannot both become the single entry.
    has_main = any(
        e.entry_id != entry.entry_id and e.version >= 2
        for e in hass.config_entries.async_entries(DOMAIN)
    )
    legacy_rooms = entry.data.get("rooms", [])

    if has_main:
        _LOGGER.info("Removing old per-area RoomControl entry '%s'", entry.title)
        hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))
        migrated = False
    else:
        hass.config_entries.async_update_entry(
            entry, data={}, title=TITLE, unique_id=DOMAIN, version=2
        )
        migrated = True

    # Rooms that the very first versions kept in entry.data.
    if legacy_rooms:
        rooms = list(_data(hass)["rooms"])
        known = {r.get("area_id") for r in rooms}
        rooms += [r for r in legacy_rooms if r.get("area_id") and r["area_id"] not in known]
        await _async_save_rooms(hass, rooms)

    return migrated


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the light for every area."""
    if CONF_AREA_ID in entry.data:  # safety net; migration should have handled it
        return False
    _data(hass)["loaded"] = True
    memory = Memory(hass)
    await memory.async_load()
    memory.start()
    _data(hass)["memory"] = memory  # first: everything below reads its state back from it
    clocks = ClockManager(hass)
    _data(hass)["clocks"] = clocks
    vacuums = VacuumManager(hass)
    _data(hass)["vacuums"] = vacuums  # before the platforms: the switch needs it
    locks = LockManager(hass)
    await locks.async_load()
    _data(hass)["locks"] = locks
    learn = LearnStore(hass)
    await learn.async_load()
    _data(hass)["learn"] = learn
    cover_memory = CoverMemory(hass)
    await cover_memory.async_load()
    cover_memory.start()
    _data(hass)["cover_memory"] = cover_memory  # before the platforms: cover/sensor read it
    from .light import async_load_fans_applied  # noqa: PLC0415

    await async_load_fans_applied(hass)
    # 2.2.0: the "Vakantie soort" select is gone (Vakantie and Verlof are switches now).
    ent_reg = er.async_get(hass)
    if old_select := ent_reg.async_get_entity_id("select", DOMAIN, f"{DOMAIN}_vacation_kind"):
        ent_reg.async_remove(old_select)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    from .device_learning import DeviceLearning  # noqa: PLC0415

    device_learning = DeviceLearning(hass)
    await device_learning.async_load()
    _data(hass)["device_learning"] = device_learning
    from .device_watch import DeviceWatch  # noqa: PLC0415

    device_watch = DeviceWatch(hass, device_learning)
    device_learning.on_done = device_watch.run_done
    _data(hass)["device_watch"] = device_watch
    from .offpay import OffPay  # noqa: PLC0415

    offpay = OffPay(hass, device_learning)
    await offpay.async_load()
    _data(hass)["offpay"] = offpay

    from .nordpool_prices import NordPoolPrices  # noqa: PLC0415

    nordpool = NordPoolPrices(hass)
    _data(hass)["nordpool"] = nordpool

    @callback
    def _learning_start(_hass: HomeAssistant) -> None:
        device_learning.start()
        device_watch.start()
        offpay.start()
        nordpool.start()

    async_at_started(hass, _learning_start)
    clocks.start()
    locks.start()
    await vacuums.async_start()
    full_control = FullControl(hass)
    full_control.start()
    _data(hass)["full_control"] = full_control
    smoke = SmokeManager(hass)
    _data(hass)["smoke"] = smoke
    smoke.start()
    doorbells = DoorbellManager(hass)
    _data(hass)["doorbells"] = doorbells
    doorbells.start()
    alarm = AlarmAutomation(hass)
    _data(hass)["alarm"] = alarm
    alarm.start()
    lamp_sync = LampSync(hass, _async_save_rooms)
    _data(hass)["lamp_sync"] = lamp_sync
    lamp_sync.start()
    room_switches = RoomSwitches(hass)
    _data(hass)["room_switches"] = room_switches
    await room_switches.async_load()
    room_switches.start()
    energy = Energy(hass)
    _data(hass)["energy"] = energy
    await energy.async_load()
    energy.start()
    from .planner import Planner  # noqa: PLC0415

    planner = Planner(hass)
    _data(hass)["planner"] = planner
    await planner.async_load()
    planner.start()
    from .energy_meter import EnergyMeter  # noqa: PLC0415

    meter = EnergyMeter(hass)
    _data(hass)["meter"] = meter
    await meter.async_load()
    meter.start()
    from .battery import HomeBattery  # noqa: PLC0415

    battery = HomeBattery(hass)
    _data(hass)["battery"] = battery
    await battery.async_load()
    battery.start()
    tags = Tags(hass)
    _data(hass)["tags"] = tags
    tags.start()
    _setup_entity_id_prefix(hass, entry)
    return True


@callback
def _setup_entity_id_prefix(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """All entities get <domain>.roomcontrol_<...>: now (shortly after the
    platforms added them) and after every config change (new entities)."""
    pending: list[Any] = []

    @callback
    def _run(_now: Any = None) -> None:
        pending.clear()
        async_prefix_entity_ids(hass, entry.entry_id)

    @callback
    def _soon(*_: Any) -> None:
        if not pending:
            pending.append(async_call_later(hass, 2, _run))

    @callback
    def _cancel() -> None:
        for unsub in pending:
            unsub()
        pending.clear()

    _soon()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_UPDATED, _soon))
    entry.async_on_unload(_cancel)


def _bundle_version() -> str:
    """Short hash of the built panel (changes with every build), else VERSION."""
    import hashlib

    try:
        with open(os.path.join(FRONTEND_DIR, "roomcontrol-panel.js"), "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:10]
    except OSError:
        return VERSION


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the lights; room config stays in storage."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        _data(hass)["loaded"] = False
        if (full_control := _data(hass).pop("full_control", None)) is not None:
            full_control.stop()
        if (cover_memory := _data(hass).pop("cover_memory", None)) is not None:
            cover_memory.stop()
        if (clocks := _data(hass).pop("clocks", None)) is not None:
            clocks.shutdown()
        if (device_learning := _data(hass).pop("device_learning", None)) is not None:
            device_learning.shutdown()
        if (nordpool := _data(hass).pop("nordpool", None)) is not None:
            nordpool.shutdown()
        if (device_watch := _data(hass).pop("device_watch", None)) is not None:
            device_watch.shutdown()
        if (offpay := _data(hass).pop("offpay", None)) is not None:
            offpay.shutdown()
        if (vacuums := _data(hass).pop("vacuums", None)) is not None:
            vacuums.stop()
        if (locks := _data(hass).pop("locks", None)) is not None:
            locks.stop()
        if (smoke := _data(hass).pop("smoke", None)) is not None:
            smoke.stop()
        if (doorbells := _data(hass).pop("doorbells", None)) is not None:
            doorbells.stop()
        if (alarm := _data(hass).pop("alarm", None)) is not None:
            alarm.stop()
        if (lamp_sync := _data(hass).pop("lamp_sync", None)) is not None:
            lamp_sync.stop()
        if (room_switches := _data(hass).pop("room_switches", None)) is not None:
            room_switches.stop()
        if (energy := _data(hass).pop("energy", None)) is not None:
            energy.stop()
        if (planner := _data(hass).pop("planner", None)) is not None:
            planner.shutdown()
        if (battery := _data(hass).pop("battery", None)) is not None:
            battery.shutdown()
        if (meter := _data(hass).pop("meter", None)) is not None:
            meter.shutdown()
        nspanel_stop(hass)
        if (tags := _data(hass).pop("tags", None)) is not None:
            tags.stop()
        if (memory := _data(hass).pop("memory", None)) is not None:
            await memory.async_stop()
    return unloaded


# ── WebSocket API ───────────────────────────────────────────────────────────


def _history_days(hass: HomeAssistant) -> int:
    """Days of history the recorder keeps (10 when unknown)."""
    try:
        from homeassistant.components.recorder import get_instance

        return int(get_instance(hass).keep_days)
    except Exception:  # noqa: BLE001 - recorder not loaded / older HA
        return 10


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get_config"})
@callback
def ws_get_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the rooms, the global settings, and whether automation is running."""
    data = _data(hass)
    connection.send_result(
        msg["id"],
        {
            "rooms": data["rooms"],
            "settings": data["settings"],
            "version": VERSION,
            # How many days of history Home Assistant keeps (recorder purge_keep_days).
            "history_days": _history_days(hass),
            # Without a loaded config entry nothing reacts to motion,
            # schedules, etc. (rooms without devices are simply unmanaged).
            "active": bool(data.get("loaded")),
            # Default texts (Teksten) in Home Assistant's language, for the panel.
            "text_defaults": default_texts(hass),
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_config",
        vol.Required("config"): vol.Schema(
            {vol.Optional("rooms"): [dict], vol.Optional("settings"): dict},
            extra=vol.ALLOW_EXTRA,
        ),
    }
)
@websocket_api.async_response
async def ws_set_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist rooms and/or settings to .storage (what is left out is kept)."""
    rooms = msg["config"].get("rooms")
    settings = msg["config"].get("settings")
    if rooms is not None and any(not r.get("area_id") for r in rooms):
        connection.send_error(msg["id"], "invalid_format", "Every room needs an area_id")
        return
    await _async_save(hass, rooms=rooms, settings=settings)
    _LOGGER.debug("RoomControl config saved")
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_dim",
        vol.Required("dim"): bool,
        vol.Optional("area_id"): str,
    }
)
@websocket_api.async_response
async def ws_set_dim(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Dim one room (area_id) or all configured, visible rooms to 1%, or restore."""
    entities = _data(hass).get("entities", {})
    if "area_id" in msg:
        targets = [entities[msg["area_id"]]] if msg["area_id"] in entities else []
    else:
        configured = set(all_dim_rooms(hass))
        targets = [e for a, e in entities.items() if a in configured and e.follows_dim]
    for entity in targets:
        await entity.async_set_dim(msg["dim"])
    connection.send_result(msg["id"], {"rooms": [e._area_id for e in targets]})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_manual",
        vol.Required("area_id"): str,
        # minutes of manual control; omitted = the room's duration; 0 = stop
        vol.Optional("minutes"): vol.All(vol.Coerce(float), vol.Range(min=0, max=480)),
    }
)
@callback
def ws_set_manual(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Start or stop manual control of a room (RoomControl does nothing meanwhile)."""
    entity = _data(hass).get("entities", {}).get(msg["area_id"])
    if entity is None:
        connection.send_error(msg["id"], "not_found", "Unknown room")
        return
    entity.async_set_manual(msg.get("minutes"))
    connection.send_result(msg["id"], {"manual_until": entity.extra_state_attributes.get("manual_until")})


PANEL_SERVICES = {
    "light": ("turn_on", "turn_off"),
    "cover": ("open_cover", "close_cover", "stop_cover", "set_cover_position"),
    "lock": ("lock", "unlock", "open"),
    "switch": ("turn_on", "turn_off"),  # a room's switches (room → Switches)
    "remote": ("turn_on", "turn_off"),  # a room's switches can be remotes (e.g. an NVIDIA Shield)
}


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/call_service",
        vol.Required("domain"): vol.In(list(PANEL_SERVICES)),
        vol.Required("service"): str,
        vol.Required("entity_id"): vol.Any(str, [str]),
        vol.Optional("data", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_call_service(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Switch lamps / move curtains from the panel as RoomControl (full control allows it)."""
    domain, service = msg["domain"], msg["service"]
    if service not in PANEL_SERVICES[domain]:
        connection.send_error(msg["id"], "invalid_format", f"{domain}.{service} is not allowed")
        return
    ids = [msg["entity_id"]] if isinstance(msg["entity_id"], str) else list(msg["entity_id"])
    known: set[str] = set()
    for room in _data(hass)["rooms"]:
        known.update(l.get("entity_id") for l in room.get("lights", []) or [] if isinstance(l, dict))
        known.update(c for c in room.get("covers", []) or [] if c)
        known.update(l.get("entity_id") for l in room.get("locks", []) or [] if isinstance(l, dict))
        known.update(sw.get("entity_id") for sw in room.get("switches", []) or [] if isinstance(sw, dict))
    own = {
        s.entity_id for s in hass.states.async_all(domain)
        if s.attributes.get("roomcontrol_area") is not None
    }
    if not ids or any(e not in known and e not in own for e in ids):
        connection.send_error(msg["id"], "not_found", "Not a lamp, curtain, lock or switch of a RoomControl room")
        return
    if domain in ("switch", "remote") and service == "turn_off" and (blocked := never_off(hass) & set(ids)):
        connection.send_error(msg["id"], "not_allowed", f"{', '.join(sorted(blocked))} may never go off")
        return
    data = {k: v for k, v in msg["data"].items() if k != "entity_id"}
    if domain == "lock":
        await hass.services.async_call("lock", service, {"entity_id": ids, **data}, blocking=True)
    else:
        await rc_call(hass, domain, service, {"entity_id": ids, **data})
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/restore_auto",
        vol.Required("area_id"): str,
        vol.Optional("lamps"): [str],
    }
)
@callback
def ws_restore_auto(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Brightness set by hand back to what RoomControl wants (panel "herstel")."""
    entity = _data(hass).get("entities", {}).get(msg["area_id"])
    if entity is not None:
        entity.restore_auto(msg.get("lamps"))
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/announce",
        vol.Required("message"): str,
        vol.Optional("areas"): [str],
    }
)
@websocket_api.async_response
async def ws_announce(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel test message: speak it on the speakers that take part now."""
    players = await async_announce(hass, msg["message"], msg.get("areas"))
    nspanel_message(hass, "announce", msg["message"])
    connection.send_result(msg["id"], {"players": players})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/test_text",
        vol.Required("message"): str,
        vol.Required("channel"): vol.In(["spoken", "notify"]),
        vol.Optional("kind", default="announce"): str,
    }
)
@websocket_api.async_response
async def ws_test_text(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel "Teksten": try a text the way it really goes out — spoken on the
    speakers (with the volume of `kind`), or as a Home Assistant notification."""
    if msg["channel"] == "spoken":
        players = await async_announce(hass, msg["message"], kind=msg["kind"])
        connection.send_result(msg["id"], {"players": players})
        return
    from homeassistant.components import persistent_notification

    persistent_notification.async_create(
        hass, msg["message"], title="RoomControl (test)", notification_id=f"{DOMAIN}_text_test"
    )
    connection.send_result(msg["id"], {"sent": True})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/alarm_status"})
@callback
def ws_alarm_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """The Alarm page: state, time slot now, distance, persons and what happened."""
    alarm = _data(hass).get("alarm")
    connection.send_result(msg["id"], alarm.status() if alarm else {})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/energy_status"})
@callback
def ws_energy_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Power per room and phase, and whether the car is charging."""
    energy = _data(hass).get("energy")
    connection.send_result(msg["id"], energy.status() if energy else {})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/devices", vol.Required("area_id"): str, vol.Optional("forget"): str,
     vol.Optional("trial"): vol.In(["start", "stop"]), vol.Optional("key"): str}
)
@callback
def ws_devices(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel: what RoomControl learned about the room's metered devices; "forget": learn one again."""
    learning = _data(hass).get("device_learning")
    if learning is None:
        connection.send_result(msg["id"], {"devices": []})
        return
    if (key := msg.get("forget")) and key.startswith(f"{msg['area_id']}|"):
        learning.forget(key)
    offpay = _data(hass).get("offpay")
    if offpay is not None and (key := msg.get("key")) and key.startswith(f"{msg['area_id']}|") and msg.get("trial"):
        offpay.start_trial(key) if msg["trial"] == "start" else offpay.stop_trial(key)
    devices = learning.profiles(msg["area_id"])
    if offpay is not None:
        for device in devices:
            if "|switch:" in device["key"]:
                try:
                    from .usage import usage  # noqa: PLC0415

                    device["offpay"] = offpay.analysis(device["key"])
                    device["usage"] = usage(offpay, device["key"])
                except Exception as err:  # noqa: BLE001 - never break the panel
                    _LOGGER.warning("Off-pay analysis of %s failed: %s", device["key"], err)
            else:
                device["kind"], device["kind_guessed"] = offpay.kind(device["key"])
    connection.send_result(msg["id"], {"devices": devices})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/tags", vol.Optional("test"): int}
)
@websocket_api.async_response
async def ws_tags(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel: Home Assistant's tags and the last scan; "test": run rule n as if scanned."""
    result: dict[str, Any] = {}
    if (n := msg.get("test")) is not None:
        rules = tag_rules(hass)
        result["ran"] = await async_run_rule(hass, rules[n]) if 0 <= n < len(rules) else None
    tags: list[dict[str, Any]] = []
    try:
        from homeassistant.components.tag import TAG_DATA  # noqa: PLC0415

        storage = hass.data.get(TAG_DATA)
        items = storage.async_items() if storage is not None else []
        for item in items:
            tag_id = item.get("id") or item.get("tag_id")
            tags.append({"id": tag_id, "name": item.get("name") or "", "last_scanned": item.get("last_scanned")})
    except Exception:  # noqa: BLE001 - older/newer Home Assistant: the panel falls back to tag/list
        tags = []
    tracker = _data(hass).get("tags")
    connection.send_result(msg["id"], {**result, "tags": tags, "last": tracker.last if tracker else None})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/nspanel", vol.Optional("action", default="list"): vol.In(["list", "test", "clear"]),
     vol.Optional("message"): str, vol.Optional("target"): str}
)
@websocket_api.async_response
async def ws_nspanel(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel: the NSPanels found; "test" shows a message on the chosen ones."""
    if msg["action"] == "test":
        shown = await nspanel_show(hass, "RoomControl", msg.get("message") or "Test",
                                   panels=target_panels(hass, msg.get("target") or "all"))
        connection.send_result(msg["id"], {"shown": shown, "found": found_panels(hass)})
        return
    if msg["action"] == "clear":
        await nspanel_clear(hass)
    connection.send_result(msg["id"], {"found": found_panels(hass), "chosen": chosen_panels(hass)})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/solar_forecasts"})
@websocket_api.async_response
async def ws_solar_forecasts(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel: the solar forecast integrations this Home Assistant has."""
    from .solar_forecast import async_list  # noqa: PLC0415

    energy = _data(hass).get("energy")
    if energy is not None:
        await energy.async_refresh_sun()
    connection.send_result(msg["id"], {"forecasts": await async_list(hass),
                                       "periods": len(energy.sun) if energy is not None else 0})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/ev_test", vol.Required("event"): vol.In(["started", "stopped", "full", "cheap"])}
)
@websocket_api.async_response
async def ws_ev_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel "Test": one car message, sent on the chosen channels."""
    energy = _data(hass).get("energy")
    if energy is None:
        connection.send_result(msg["id"], {"done": False})
        return
    status = energy.status()
    cfg = _data(hass).get("settings", {}).get("energy") or {}
    result = await energy.notifier.async_test(cfg, msg["event"], status.get("car"), status.get("price"))
    connection.send_result(msg["id"], {"done": True, **result})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/alarm_test", vol.Required("state"): str}
)
@websocket_api.async_response
async def ws_alarm_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Panel "Test": the text of a state, spoken and/or sent as a message."""
    alarm = _data(hass).get("alarm")
    result = await alarm.test_state(msg["state"]) if alarm is not None else {}
    connection.send_result(msg["id"], {"done": alarm is not None, **result})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/smoke_clear"})
@callback
def ws_smoke_clear(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """"Alles veilig": end the smoke state, RoomControl takes over again."""
    smoke = _data(hass).get("smoke")
    if smoke is not None:
        smoke.clear()
    connection.send_result(msg["id"], {"success": True, "status": smoke.status() if smoke else None})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/forget_learned",
        vol.Required("area_id"): str,
        vol.Required("what"): vol.In(["grace_extra", "brightness", "sessions", "motion"]),
    }
)
@callback
def ws_forget_learned(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Forget what a room learned (one kind), so it starts over."""
    learn = _data(hass).get("learn")
    if learn is not None:
        learn.forget(msg["area_id"], msg["what"])
    entity = _data(hass).get("entities", {}).get(msg["area_id"])
    if entity is not None:
        entity.refresh_state()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_debug",
        vol.Required("area_id"): str,
        vol.Optional("day"): vol.All(int, vol.Range(min=0, max=6)),
        vol.Optional("item"): vol.Any(str, None),
        vol.Optional("limit"): vol.All(int, vol.Range(min=1, max=6000)),
    }
)
@callback
def ws_get_debug(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """A room's debug log, newest first. With "day" (0 = today): that day's
    log (of one "item") with the rules per decision, the items and the counts
    per day (debug tab); without: the newest "limit" entries."""
    entity = _data(hass).get("entities", {}).get(msg["area_id"])
    if entity is None:
        connection.send_result(msg["id"], {"entries": [], "now": None, "upcoming": [], "items": [], "counts": []})
        return
    result: dict[str, Any] = {"now": entity.debug_now(), "upcoming": entity.upcoming()}
    if "day" in msg:
        result.update(entity.debug_day(msg["day"], msg.get("item") or None))
        result["items"] = entity.debug_items()
    else:
        result["entries"] = entity.debug_log(msg.get("limit", 300))
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/energy_overview"})
@callback
def ws_energy_overview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Energy → Overzicht: the house now and today, rooms, phases, base load."""
    meter = _data(hass).get("meter")
    connection.send_result(msg["id"], meter.overview() if meter is not None else {})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/energy_bill", vol.Optional("month"): vol.Match(r"^\d{4}-\d{2}$")}
)
@websocket_api.async_response
async def ws_energy_bill(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Energy → Rekening: a month so far, the forecast and the advance payment."""
    meter = _data(hass).get("meter")
    connection.send_result(msg["id"], await meter.async_bill(msg.get("month")) if meter is not None else {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/energy_coach",
        vol.Optional("apply"): str,
        vol.Optional("dismiss"): str,
        vol.Optional("reset"): bool,
    }
)
@websocket_api.async_response
async def ws_energy_coach(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Energy → Besparen: this week's tips; apply or dismiss one."""
    meter = _data(hass).get("meter")
    if meter is None:
        connection.send_result(msg["id"], {})
        return
    result: dict[str, Any] = {}
    if msg.get("apply"):
        result["applied"] = await meter.async_apply(msg["apply"])
    if msg.get("dismiss"):
        meter.dismiss(msg["dismiss"])
    if msg.get("reset"):
        meter.dismissed = []
        meter._save()
    connection.send_result(msg["id"], {**meter.coach(), **result})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/battery"})
@callback
def ws_battery(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Energy → Thuisbatterij: live values, the plan and the last simulation."""
    battery = _data(hass).get("battery")
    connection.send_result(msg["id"], battery.status() if battery is not None else {})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/battery_sim",
        vol.Optional("days", default=90): vol.All(int, vol.Range(min=7, max=365)),
        vol.Optional("sizes"): [
            {vol.Required("kwh"): vol.Coerce(float), vol.Required("kw"): vol.Coerce(float),
             vol.Optional("price"): vol.Any(None, vol.Coerce(float))}
        ],
    }
)
@websocket_api.async_response
async def ws_battery_sim(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run the simulation: what would these batteries have brought?"""
    battery = _data(hass).get("battery")
    if battery is None:
        connection.send_error(msg["id"], "not_ready", "RoomControl is not loaded")
        return
    connection.send_result(msg["id"], await battery.async_simulate(msg["days"], msg.get("sizes")))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/battery_test",
        vol.Required("action"): vol.In(["charge", "discharge", "self", "idle"]),
        vol.Optional("power", default=500): vol.All(int, vol.Range(min=0, max=20000)),
    }
)
@websocket_api.async_response
async def ws_battery_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Test the battery's steering for one minute, then back to its own mode."""
    battery = _data(hass).get("battery")
    if battery is None:
        connection.send_error(msg["id"], "not_ready", "RoomControl is not loaded")
        return
    await battery.async_test(msg["action"], msg["power"])
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/plan"})
@callback
def ws_plan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Energy → Plannen: the next 24 hours and the plan per flexible device."""
    planner = _data(hass).get("planner")
    connection.send_result(msg["id"], planner.status() if planner is not None else {"devices": [], "rows": []})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/vacuum_start", vol.Required("area_id"): str}
)
@websocket_api.async_response
async def ws_vacuum_start(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """"Clean now" from the panel: the room's vacuum, with the alarm handling."""
    manager = _data(hass).get("vacuums")
    ok = await manager.start_clean(area_id=msg["area_id"]) if manager is not None else False
    if not ok:
        connection.send_error(msg["id"], "not_found", "No vacuum for this room or it could not start")
        return
    connection.send_result(msg["id"], {"success": True})
