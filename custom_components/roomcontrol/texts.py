"""Texts RoomControl speaks or sends (general setting `texts`, adjustable in the panel).

A text that is missing or empty in the settings uses its default, in Dutch
when Home Assistant's language is Dutch, else in English. Placeholders in
braces are filled in: {room}, {name}, {hours} (or in Dutch {ruimte}, {naam},
{uren}). An unknown placeholder stays
as it is (a typo never breaks a smoke warning).
"""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .const import DOMAIN

SETTING_TEXTS = "texts"

# key: (Dutch, English, placeholders)
DEFAULT_TEXTS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "smoke_spoken": ("Let op. Rook gedetecteerd in {room}.", "Attention. Smoke detected in {room}.", ("room",)),
    "smoke_notify": ("Rook gedetecteerd in {room}.", "Smoke detected in {room}.", ("room",)),
    "smoke_battery": ("De batterij van rookmelder {name} is bijna leeg.", "The battery of smoke detector {name} is low.", ("name",)),
    "smoke_offline": (
        "Rookmelder {name} is al {hours} uur niet bereikbaar.",
        "Smoke detector {name} has been unavailable for {hours} hours.", ("name", "hours"),
    ),
    "doorbell_spoken": ("Er staat iemand bij de deur, {room}.", "Someone is at the door, {room}.", ("room",)),
    "doorbell_notify": ("Er wordt aangebeld ({room}).", "The doorbell rang ({room}).", ("room",)),
    "anomaly_motion": (
        "Beweging in {room} op een tijdstip waarop daar normaal niemand is.",
        "Motion in {room} at a time when nobody is normally there.", ("room",),
    ),
    "anomaly_lights_on": (
        "In {room} branden de lampen al {hours} uur zonder beweging.",
        "The lights in {room} have been on for {hours} hours without motion.", ("room", "hours"),
    ),
}


# Dutch names that work too in own texts: {ruimte}, {naam}, {uren}.
DUTCH_PLACEHOLDERS = {"room": "ruimte", "name": "naam", "hours": "uren"}


def _dutch(hass: HomeAssistant) -> bool:
    return (hass.config.language or "").startswith("nl")


def default_texts(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    """Defaults in Home Assistant's language, with their placeholders (panel)."""
    dutch = _dutch(hass)
    return {key: {"text": nl if dutch else en, "placeholders": list(ph)} for key, (nl, en, ph) in DEFAULT_TEXTS.items()}


def text(hass: HomeAssistant, key: str, **values: Any) -> str:
    """The text for `key` (own text from the settings, else the default), filled in."""
    nl, en, _ph = DEFAULT_TEXTS[key]
    own = (hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_TEXTS) or {}).get(key)
    template = own.strip() if isinstance(own, str) and own.strip() else (nl if _dutch(hass) else en)
    for name, value in values.items():
        template = template.replace("{" + name + "}", str(value))
        if (alias := DUTCH_PLACEHOLDERS.get(name)) is not None:
            template = template.replace("{" + alias + "}", str(value))
    return template
