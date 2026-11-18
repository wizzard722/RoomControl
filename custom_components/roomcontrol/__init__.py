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
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store

from .clocks import ClockManager
from .locks import LockManager
from .learn import LearnStore
from .smoke import SmokeManager
from .doorbell import DoorbellManager
from .announce import async_announce
from .texts import default_texts
from .vacuums import VacuumManager
from .control import FullControl, rc_call
from .entity_ids import async_prefix_entity_ids
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

PLATFORMS = [Platform.LIGHT, Platform.COVER, Platform.FAN, Platform.SWITCH, Platform.BUTTON, Platform.LOCK, Platform.NOTIFY]
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
        data["rooms"] = rooms
    if settings is not None:
        data["settings"] = {**DEFAULT_SETTINGS, **settings}
    await data["store"].async_save({"rooms": data["rooms"], "settings": data["settings"]})
    async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED)


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

    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_set_config)
    websocket_api.async_register_command(hass, ws_set_dim)
    websocket_api.async_register_command(hass, ws_set_manual)
    websocket_api.async_register_command(hass, ws_call_service)
    websocket_api.async_register_command(hass, ws_get_debug)
    websocket_api.async_register_command(hass, ws_forget_learned)
    websocket_api.async_register_command(hass, ws_smoke_clear)
    websocket_api.async_register_command(hass, ws_restore_auto)
    websocket_api.async_register_command(hass, ws_announce)

    async def _announce_service(call: ServiceCall) -> ServiceResponse:
        areas = call.data.get("areas")
        if isinstance(areas, str):
            areas = [areas]
        players = await async_announce(hass, call.data["message"], areas or None)
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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
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
        if (clocks := _data(hass).pop("clocks", None)) is not None:
            clocks.stop()
        if (vacuums := _data(hass).pop("vacuums", None)) is not None:
            vacuums.stop()
        if (locks := _data(hass).pop("locks", None)) is not None:
            locks.stop()
        if (smoke := _data(hass).pop("smoke", None)) is not None:
            smoke.stop()
        if (doorbells := _data(hass).pop("doorbells", None)) is not None:
            doorbells.stop()
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
        configured = {
            r["area_id"] for r in _data(hass)["rooms"]
            if r.get("lights") and not r.get("hidden")
        }
        targets = [e for a, e in entities.items() if a in configured]
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
    own = {
        s.entity_id for s in hass.states.async_all(domain)
        if s.attributes.get("roomcontrol_area") is not None
    }
    if not ids or any(e not in known and e not in own for e in ids):
        connection.send_error(msg["id"], "not_found", "Not a lamp, curtain or lock of a RoomControl room")
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
    connection.send_result(msg["id"], {"players": players})


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
    {vol.Required("type"): f"{DOMAIN}/get_debug", vol.Required("area_id"): str}
)
@callback
def ws_get_debug(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """A room's debug log: why bundles did or did not go on/off, newest first."""
    entity = _data(hass).get("entities", {}).get(msg["area_id"])
    connection.send_result(msg["id"], {
        "entries": entity.debug_log() if entity is not None else [],
        "now": entity.debug_now() if entity is not None else None,
    })


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
