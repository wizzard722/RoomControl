"""Messages to persons: each person's device (e.g. a phone).

General setting "person_notify": {person entity: "notify.<service>" | "none"}.
"none": the person gets no messages on a device. A person without a choice uses the Home Assistant app on their own device: the device
of one of the person's device trackers, whose app registered the notify
service mobile_app_<device name>.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import slugify

from .const import DOMAIN

SETTING_PERSON_NOTIFY = "person_notify"


@callback
def auto_notify_service(hass: HomeAssistant, person: str) -> str | None:
    """notify.mobile_app_<device> of one of the person's device trackers."""
    st = hass.states.get(person)
    trackers = st.attributes.get("device_trackers") or [] if st is not None else []
    ent_reg, dev_reg = er.async_get(hass), dr.async_get(hass)
    for tracker in trackers:
        entry = ent_reg.async_get(tracker)
        device = dev_reg.async_get(entry.device_id) if entry and entry.device_id else None
        if device is None:
            continue
        for name in (device.name_by_user, device.name):
            if name and hass.services.has_service("notify", f"mobile_app_{slugify(name)}"):
                return f"notify.mobile_app_{slugify(name)}"
    return None


@callback
def person_notify_service(hass: HomeAssistant, person: str) -> str | None:
    """The notify service that reaches this person (chosen, else automatic)."""
    chosen = (hass.data.get(DOMAIN, {}).get("settings", {}).get(SETTING_PERSON_NOTIFY) or {}).get(person)
    if chosen == "none":
        return None  # chosen: no device for this person
    if isinstance(chosen, str) and chosen.startswith("notify."):
        return chosen
    return auto_notify_service(hass, person)
