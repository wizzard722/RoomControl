"""Smoke detectors (general settings): what RoomControl does when there is smoke.

When one of the chosen detectors (binary_sensor, device class smoke) goes on,
smoke becomes "active" for the whole house, until someone confirms "Alles
veilig" in the panel. Once, at the start (each action can be switched off):
- lights: every lamp of every room fully on, white where the lamp can;
- fans: off (so smoke is not drawn through the house);
- covers: open;
- locks: opened, but only when someone is home (off by default);
- media: stopped; the announcement speakers (see announce.py) say where the smoke is;
- vacuum: back to its dock;
- switches: the chosen switches off (espresso machine, heater, TV, …);
  at "Alles veilig" the ones that were on go on again.
While active, RoomControl does nothing automatic (rooms act as in manual
control, alarm clocks, vacuum moments and lock times wait).

Maintenance (also an action): a notification when a detector's battery is
below BATTERY_LOW % or it has been unavailable for OFFLINE_HOURS.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .room_switches import never_off, switches_for
from .texts import text
from .const import CONF_COVERS, CONF_MEDIA_PLAYERS, DOMAIN, SIGNAL_CONFIG_UPDATED
from .announce import async_announce
from .nspanel import nspanel_message
from .control import rc_call
from .rooms import anyone_home, managed_areas, room_fans, room_lights, room_locks, supports_kelvin

_LOGGER = logging.getLogger(__name__)

SETTING_SMOKE_DETECTORS = "smoke_detectors"
SETTING_SMOKE_ACTIONS = "smoke_actions"
SETTING_SMOKE_TTS = "smoke_tts"
# switch.* entities that go off at smoke (action "switches").
SETTING_SMOKE_SWITCHES = "smoke_switches"
SMOKE_ACTIONS_DEFAULT = {
    "lights": True, "fans": True, "covers": True, "locks": False,
    "media": True, "vacuum": True, "switches": True, "maintenance": True,
}
SIGNAL_SMOKE = "roomcontrol_smoke"
SMOKE_KELVIN = 4000
BATTERY_LOW = 20  # %
OFFLINE_HOURS = 24
MAINTENANCE_INTERVAL = timedelta(hours=1)
MAINTENANCE_REPEAT = timedelta(hours=24)


def smoke_active(hass: HomeAssistant) -> bool:
    manager = hass.data.get(DOMAIN, {}).get("smoke")
    return manager is not None and manager.active


def battery_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """The battery sensor on the same device as `entity_id` (None: none)."""
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    if entry is None or entry.device_id is None:
        return None
    for other in er.async_entries_for_device(ent_reg, entry.device_id):
        st = hass.states.get(other.entity_id)
        cls = other.device_class or other.original_device_class or (st.attributes.get("device_class") if st else None)
        if cls == "battery" and other.entity_id.split(".")[0] in ("sensor", "binary_sensor"):
            return other.entity_id
    return None


class SmokeManager:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.active = False
        self.since: datetime | None = None
        self.areas: list[str] = []
        self._unsubs: list[CALLBACK_TYPE] = []
        self._unsub_track: CALLBACK_TYPE | None = None
        self._tracked: tuple[str, ...] = ()
        self._maintenance_sent: dict[str, datetime] = {}
        # Switches that were on when the smoke started (on again at "Alles veilig").
        self._switches_were_on: list[str] = []
        # Since when RoomControl watches: right after a restart the detectors'
        # integrations may not be loaded yet, so "no state" is not "offline".
        self._watch_since = dt_util.utcnow()

    # ── settings ───────────────────────────────────────────────────────────

    def _settings(self) -> dict[str, Any]:
        return self.hass.data.get(DOMAIN, {}).get("settings", {})

    def detectors(self) -> list[str]:
        return [d for d in self._settings().get(SETTING_SMOKE_DETECTORS, []) or [] if d]

    def action(self, key: str) -> bool:
        actions = self._settings().get(SETTING_SMOKE_ACTIONS) or {}
        return bool(actions.get(key, SMOKE_ACTIONS_DEFAULT[key]))

    # ── lifecycle ──────────────────────────────────────────────────────────

    def _memory_data(self) -> dict[str, Any] | None:
        """Smoke stays active across a restart until "All safe" (see memory.py)."""
        if not self.active and not self._maintenance_sent:
            return None
        return {
            "active": self.active,
            "since": self.since.isoformat() if self.since else None,
            "areas": list(self.areas),
            "switches_were_on": list(self._switches_were_on),
            "maintenance_sent": {k: v.isoformat() for k, v in self._maintenance_sent.items()},
        }

    @callback
    def _restore_memory(self) -> None:
        mem = self.hass.data.get(DOMAIN, {}).get("memory")
        if mem is None:
            return
        data = mem.get("smoke")
        self._unsubs.append(mem.register("smoke", self._memory_data))
        if not isinstance(data, dict):
            return
        sent = data.get("maintenance_sent") or {}
        self._maintenance_sent = {
            k: t for k, v in sent.items() if isinstance(v, str) and (t := dt_util.parse_datetime(v)) is not None
        }
        if data.get("active"):
            # Smoke before the restart and nobody pressed "All safe" yet: still active.
            self.active = True
            self.since = dt_util.parse_datetime(data.get("since") or "") or dt_util.utcnow()
            self.areas = [a for a in data.get("areas") or [] if isinstance(a, str)]
            self._switches_were_on = [s for s in data.get("switches_were_on") or [] if isinstance(s, str)]
            async_dispatcher_send(self.hass, SIGNAL_SMOKE)

    @callback
    def start(self) -> None:
        self._restore_memory()
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._sync))
        self._unsubs.append(
            async_track_time_interval(self.hass, self._maintenance, MAINTENANCE_INTERVAL)
        )
        self._sync()
        self._maintenance()

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._unsub_track:
            self._unsub_track()
            self._unsub_track = None

    @callback
    def _sync(self, *_: Any) -> None:
        ids = tuple(self.detectors())
        if ids != self._tracked:
            if self._unsub_track:
                self._unsub_track()
                self._unsub_track = None
            self._tracked = ids
            if ids:
                self._unsub_track = async_track_state_change_event(self.hass, list(ids), self._on_change)
        # A detector that already reports smoke (e.g. at startup) counts too.
        for entity_id in ids:
            if (st := self.hass.states.get(entity_id)) is not None and st.state == "on":
                self._trigger(entity_id)

    @callback
    def _on_change(self, event: Event) -> None:
        new = event.data.get("new_state")
        if new is not None and new.state == "on":
            self._trigger(new.entity_id)

    # ── smoke ──────────────────────────────────────────────────────────────

    def _area_of(self, entity_id: str) -> str | None:
        entry = er.async_get(self.hass).async_get(entity_id)
        if entry is None:
            return None
        if entry.area_id:
            return entry.area_id
        if entry.device_id and (device := dr.async_get(self.hass).async_get(entry.device_id)):
            return device.area_id
        return None

    def _area_name(self, area_id: str | None) -> str:
        area = ar.async_get(self.hass).async_get_area(area_id) if area_id else None
        return area.name if area else ("?" if not area_id else area_id)

    @callback
    def _trigger(self, entity_id: str) -> None:
        area = self._area_of(entity_id)
        if area and area not in self.areas:
            self.areas.append(area)
        if self.active:
            async_dispatcher_send(self.hass, SIGNAL_SMOKE)
            return
        self.active = True
        self.since = dt_util.utcnow()
        if (mem := self.hass.data.get(DOMAIN, {}).get("memory")) is not None:
            mem.changed()
        _LOGGER.warning("Smoke detected by %s (%s)", entity_id, area)
        where = self._area_name(area)
        message = text(self.hass, "smoke_notify", room=where)
        persistent_notification.async_create(
            self.hass, message, title="RoomControl", notification_id="roomcontrol_smoke"
        )
        self.hass.bus.async_fire("roomcontrol_smoke", {"entity_id": entity_id, "area_id": area, "message": message})
        async_dispatcher_send(self.hass, SIGNAL_SMOKE)
        self.hass.async_create_task(self._async_actions(where))

    @callback
    def clear(self) -> None:
        """"Alles veilig": RoomControl takes over again."""
        if not self.active:
            return
        self.active = False
        self.since = None
        self.areas = []
        if (mem := self.hass.data.get(DOMAIN, {}).get("memory")) is not None:
            mem.changed()
        persistent_notification.async_dismiss(self.hass, "roomcontrol_smoke")
        if self._switches_were_on:
            # The devices that were on before the smoke go on again.
            switches, self._switches_were_on = self._switches_were_on, []
            self.hass.async_create_task(self._turn(switches, True))
        async_dispatcher_send(self.hass, SIGNAL_SMOKE)
        # Rooms, locks etc. look again at what they should do now.
        async_dispatcher_send(self.hass, SIGNAL_CONFIG_UPDATED)

    def status(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "since": self.since.isoformat() if self.since else None,
            "areas": list(self.areas),
            "smoke_now": [d for d in self.detectors() if (st := self.hass.states.get(d)) is not None and st.state == "on"],
        }

    async def _turn(self, entities: list[str], on: bool) -> None:
        """Switches (and remotes) on / off, each with its own domain."""
        from .room_switches import async_turn  # noqa: PLC0415

        try:
            await async_turn(self.hass, entities, on)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Smoke: switching %s failed: %s", entities, err)

    async def _call(self, domain: str, service: str, data: dict[str, Any]) -> None:
        try:
            if domain in ("light", "cover"):
                await rc_call(self.hass, domain, service, data, blocking=True)
            else:
                await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception:  # noqa: BLE001 - one failing device must not stop the rest
            _LOGGER.exception("Smoke: %s.%s failed for %s", domain, service, data.get(ATTR_ENTITY_ID))

    async def _async_actions(self, where: str) -> None:
        rooms = [
            r for r in self.hass.data.get(DOMAIN, {}).get("rooms", [])
            if r.get("area_id") in managed_areas(self.hass)
        ]
        lights = sorted({e for r in rooms for e in room_lights(self.hass, r["area_id"])})
        if self.action("lights") and lights:
            white = [e for e in lights if supports_kelvin(self.hass, e)]
            other = [e for e in lights if e not in white]
            if white:
                await self._call("light", "turn_on", {ATTR_ENTITY_ID: white, "brightness_pct": 100, "color_temp_kelvin": SMOKE_KELVIN})
            if other:
                await self._call("light", "turn_on", {ATTR_ENTITY_ID: other, "brightness_pct": 100})
        fans = sorted({f for r in rooms for f in room_fans(self.hass, r["area_id"])})
        if self.action("fans") and fans:
            await self._call("fan", "turn_off", {ATTR_ENTITY_ID: fans})
        blocked = never_off(self.hass)
        switches = [s for s in self._settings().get(SETTING_SMOKE_SWITCHES, []) or [] if s and s not in blocked]
        # Plus the rooms' switches that go off at smoke.
        switches += [s for s in switches_for(self.hass, "smoke") if s not in switches]
        if self.action("switches") and switches:
            self._switches_were_on = [
                x for x in switches if (st := self.hass.states.get(x)) is not None and st.state == "on"
            ]
            await self._turn(switches, False)
        covers = sorted({c for r in rooms for c in r.get(CONF_COVERS, []) or [] if c})
        if self.action("covers") and covers:
            await self._call("cover", "open_cover", {ATTR_ENTITY_ID: covers})
        locks = sorted({lock["entity_id"] for r in rooms for lock in room_locks(r)})
        if self.action("locks") and locks:
            if anyone_home(self.hass):
                await self._call("lock", "unlock", {ATTR_ENTITY_ID: locks})
            else:
                _LOGGER.warning("Smoke: locks stay locked, nobody is home")
        players = sorted({p for r in rooms for p in r.get(CONF_MEDIA_PLAYERS, []) or [] if p})
        if self.action("media") and players:
            playing = [p for p in players if (st := self.hass.states.get(p)) is not None and st.state in ("playing", "paused")]
            if playing:
                await self._call("media_player", "media_stop", {ATTR_ENTITY_ID: playing})
            # Every speaker that takes part in announcements (Omroepen).
            await async_announce(self.hass, text(self.hass, "smoke_spoken", room=where), kind="smoke")
        nspanel_message(self.hass, "smoke", text(self.hass, "smoke_spoken", room=where))
        vacuums = sorted({v for r in rooms for v in r.get("vacuums", []) or [] if v})
        if self.action("vacuum") and vacuums:
            await self._call("vacuum", "return_to_base", {ATTR_ENTITY_ID: vacuums})

    # ── maintenance ────────────────────────────────────────────────────────

    @callback
    def _maintenance(self, _now: Any = None) -> None:
        if not self.action("maintenance"):
            return
        now = dt_util.utcnow()
        for detector in self.detectors():
            st = self.hass.states.get(detector)
            entry = er.async_get(self.hass).async_get(detector)
            name = (
                (st.attributes.get("friendly_name") if st else None)
                or (entry.name or entry.original_name if entry else None)
                or detector
            )
            problem: str | None = None
            if st is None or st.state in ("unavailable", "unknown"):
                # Offline only when RoomControl itself saw it away that long
                # (not counting the time before the last restart).
                since = max(st.last_changed, self._watch_since) if st else self._watch_since
                if now - since >= timedelta(hours=OFFLINE_HOURS):
                    problem = text(self.hass, "smoke_offline", name=name, hours=OFFLINE_HOURS)
            elif (battery := battery_entity(self.hass, detector)) and (bst := self.hass.states.get(battery)):
                low = bst.state == "on" if battery.startswith("binary_sensor.") else (
                    _number(bst.state) is not None and _number(bst.state) < BATTERY_LOW
                )
                if low:
                    problem = text(self.hass, "smoke_battery", name=name)
            if problem is None:
                # Also clears a notification from before a restart.
                self._maintenance_sent.pop(detector, None)
                persistent_notification.async_dismiss(self.hass, f"roomcontrol_smoke_maint_{detector}")
                continue
            last = self._maintenance_sent.get(detector)
            if last is not None and now - last < MAINTENANCE_REPEAT:
                continue
            self._maintenance_sent[detector] = now
            persistent_notification.async_create(
                self.hass, problem, title="RoomControl", notification_id=f"roomcontrol_smoke_maint_{detector}"
            )
            self.hass.bus.async_fire("roomcontrol_smoke_maintenance", {"entity_id": detector, "message": problem})


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
