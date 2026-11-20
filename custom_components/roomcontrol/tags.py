"""Home Assistant tags (NFC / QR): a scan switches chosen things.

General setting "tags": [{
  "tag_id": the tag's id in Home Assistant,
  "action": "toggle" | "on" | "off",
  "targets": [entity ids: light (also a RoomControl light bundle), switch,
              lock, cover, fan, input_boolean, media_player, scene, script],
  "persons": [person entities]}]   # optional: only they may use the tag

A scan counts as a person's when it comes from their Home Assistant user
(the companion app scans with the app's user) or from one of their
devices (the device of one of the person's device trackers). A tag with
persons does nothing for any other scan, e.g. a fixed NFC reader.

"on" = on / open / unlock, "off" = off / close / lock. "toggle": when any
target is on (open, unlocked), all go off (close, lock); else all go on.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SETTING_TAGS = "tags"
EVENT_TAG_SCANNED = "tag_scanned"

_ON = {"light": "turn_on", "switch": "turn_on", "fan": "turn_on", "input_boolean": "turn_on",
       "media_player": "turn_on", "lock": "unlock", "cover": "open_cover", "scene": "turn_on", "script": "turn_on"}
_OFF = {"light": "turn_off", "switch": "turn_off", "fan": "turn_off", "input_boolean": "turn_off",
        "media_player": "turn_off", "lock": "lock", "cover": "close_cover"}
_ACTIVE = {"on", "open", "opening", "unlocked", "unlocking", "playing", "paused", "idle"}


def tag_rules(hass: HomeAssistant) -> list[dict[str, Any]]:
    rules = hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_TAGS)
    return [r for r in rules or [] if isinstance(r, dict) and r.get("tag_id")]


def is_active(hass: HomeAssistant, entity_id: str) -> bool:
    st = hass.states.get(entity_id)
    return st is not None and st.state in _ACTIVE


async def async_run_rule(hass: HomeAssistant, rule: dict[str, Any]) -> dict[str, Any]:
    """Carry out one tag's action. Returns {"turn": "on" | "off", "targets": [...]}."""
    targets = [t for t in rule.get("targets") or [] if isinstance(t, str) and "." in t]
    action = rule.get("action") or "toggle"
    if action == "toggle":
        turn = "off" if any(is_active(hass, t) for t in targets) else "on"
    else:
        turn = "off" if action == "off" else "on"
    table = _OFF if turn == "off" else _ON
    by_call: dict[tuple[str, str], list[str]] = {}
    for target in targets:
        domain = target.split(".", 1)[0]
        if service := table.get(domain):
            by_call.setdefault((domain, service), []).append(target)
    for (domain, service), ids in by_call.items():
        try:
            await hass.services.async_call(domain, service, {ATTR_ENTITY_ID: ids}, blocking=True)
        except Exception as err:  # noqa: BLE001 - one broken device must not stop the rest
            _LOGGER.warning("Tag %s: %s.%s failed: %s", rule.get("tag_id"), domain, service, err)
    return {"turn": turn, "targets": targets}


def scan_person(hass: HomeAssistant, user_id: str | None, device_id: str | None) -> str | None:
    """The person who scanned: by Home Assistant user, else by device."""
    ent_reg = er.async_get(hass)
    for st in hass.states.async_all("person"):
        if user_id and st.attributes.get("user_id") == user_id:
            return st.entity_id
        if device_id:
            for tracker in st.attributes.get("device_trackers") or []:
                entry = ent_reg.async_get(tracker)
                if entry is not None and entry.device_id == device_id:
                    return st.entity_id
    return None


def allowed(rule: dict[str, Any], person: str | None) -> bool:
    persons = [p for p in rule.get("persons") or [] if p]
    return not persons or person in persons


class Tags:
    """Listens to tag scans and carries out the chosen actions."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsub: CALLBACK_TYPE | None = None
        self.last: dict[str, Any] | None = None  # the last scan, for the panel

    @callback
    def start(self) -> None:
        self._unsub = self.hass.bus.async_listen(EVENT_TAG_SCANNED, self._on_scan)

    @callback
    def stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _on_scan(self, event: Event) -> None:
        tag_id = event.data.get("tag_id")
        if not tag_id:
            return
        rules = [r for r in tag_rules(self.hass) if r["tag_id"] == tag_id]
        person = scan_person(self.hass, event.context.user_id, event.data.get("device_id"))
        self.last = {"tag_id": tag_id, "device_id": event.data.get("device_id"), "person": person,
                     "at": dt_util.utcnow().isoformat(), "known": bool(rules)}
        for rule in rules:
            if not allowed(rule, person):
                _LOGGER.info("Tag %s: scanned by %s, who may not use it", tag_id, person or "someone unknown")
                self.last["refused"] = True
                continue
            self.hass.async_create_task(self._run(rule))

    async def _run(self, rule: dict[str, Any]) -> None:
        result = await async_run_rule(self.hass, rule)
        _LOGGER.debug("Tag %s: %s %s", rule.get("tag_id"), result["turn"], result["targets"])
        if self.last is not None and self.last.get("tag_id") == rule.get("tag_id"):
            self.last["turn"] = result["turn"]
