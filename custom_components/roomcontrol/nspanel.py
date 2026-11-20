"""Messages on NSPanels (NSPanel Easy, ESPHome).

An NSPanel Easy panel offers the actions esphome.<panel>_notification_show
(label, message) and esphome.<panel>_notification_clear. RoomControl finds
the panels by those actions, shows its messages on them and clears them
again after a while (the panel itself keeps a message until it is cleared).

General setting "nspanel": {
  "on": bool,
  "panels": [panel names],         # [] = every panel found
  "seconds": 60,                   # how long a message stays (0: until the next)
  "sources": {"alarm": bool, "ev": bool, "smoke": bool, "doorbell": bool,
              "announce": bool}}   # which messages go to the panels (default all)
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SETTING_NSPANEL = "nspanel"
SOURCES = ("alarm", "ev", "smoke", "doorbell", "announce")
_SHOW, _CLEAR = "_notification_show", "_notification_clear"
DEFAULT_SECONDS = 60


_LABELS = {
    "nl": {"alarm": "Alarm", "ev": "Auto laden", "smoke": "Rook!", "doorbell": "Deurbel", "announce": "Bericht"},
    "en": {"alarm": "Alarm", "ev": "Car charging", "smoke": "Smoke!", "doorbell": "Doorbell", "announce": "Message"},
}


def label(hass: HomeAssistant, source: str) -> str:
    lang = "nl" if (hass.config.language or "").lower().startswith("nl") else "en"
    return _LABELS[lang].get(source, "RoomControl")


def nspanel_cfg(hass: HomeAssistant) -> dict[str, Any]:
    cfg = hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_NSPANEL)
    return cfg if isinstance(cfg, dict) else {}


@callback
def found_panels(hass: HomeAssistant) -> list[str]:
    """The NSPanel Easy panels: those with a notification_show action."""
    services = hass.services.async_services().get("esphome", {})
    return sorted(name[: -len(_SHOW)] for name in services if name.endswith(_SHOW))


@callback
def chosen_panels(hass: HomeAssistant) -> list[str]:
    found = found_panels(hass)
    chosen = [p for p in nspanel_cfg(hass).get("panels") or [] if p in found]
    return chosen or found


def _timers(hass: HomeAssistant) -> dict[str, CALLBACK_TYPE]:
    return hass.data.setdefault(DOMAIN, {}).setdefault("nspanel_timers", {})


async def async_show(hass: HomeAssistant, label: str, message: str,
                     seconds: float | None = None, panels: list[str] | None = None) -> list[str]:
    """Show a message on the panels; clear it after `seconds`. Returns the panels."""
    cfg = nspanel_cfg(hass)
    targets = panels if panels is not None else chosen_panels(hass)
    if seconds is None:
        value = cfg.get("seconds")
        seconds = float(value) if isinstance(value, (int, float)) else DEFAULT_SECONDS
    timers = _timers(hass)
    shown: list[str] = []
    for panel in targets:
        try:
            await hass.services.async_call(
                "esphome", panel + _SHOW, {"label": label[:60], "message": message}, blocking=True)
        except Exception as err:  # noqa: BLE001 - one panel offline must not stop the rest
            _LOGGER.warning("NSPanel %s: showing a message failed: %s", panel, err)
            continue
        shown.append(panel)
        if (old := timers.pop(panel, None)) is not None:
            old()
        if seconds and seconds > 0:
            @callback
            def _clear(_now: Any, panel: str = panel) -> None:
                timers.pop(panel, None)
                hass.async_create_task(async_clear(hass, [panel]))

            timers[panel] = async_call_later(hass, seconds, _clear)
    return shown


async def async_clear(hass: HomeAssistant, panels: list[str] | None = None) -> None:
    for panel in panels if panels is not None else chosen_panels(hass):
        if not hass.services.has_service("esphome", panel + _CLEAR):
            continue
        try:
            await hass.services.async_call("esphome", panel + _CLEAR, {}, blocking=True)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("NSPanel %s: clearing the message failed: %s", panel, err)


@callback
def nspanel_message(hass: HomeAssistant, source: str, message: str, title: str | None = None) -> None:
    """A RoomControl message of this kind: on the panels, when that is chosen."""
    cfg = nspanel_cfg(hass)
    if not cfg.get("on") or not message:
        return
    if (cfg.get("sources") or {}).get(source, True) is False:
        return
    if not found_panels(hass):
        return
    hass.async_create_task(async_show(hass, title or label(hass, source), message))


@callback
def stop_timers(hass: HomeAssistant) -> None:
    for unsub in _timers(hass).values():
        unsub()
    _timers(hass).clear()
