"""Entity IDs: every RoomControl entity is <domain>.roomcontrol_<...>.

Home Assistant makes an entity ID from the device and entity name (e.g.
switch.badkamer_dim, switch.generiek_vakantie). RoomControl suggests its own
ID with a prefix instead (switch.roomcontrol_badkamer_dim,
switch.roomcontrol_generiek_vakantie), for the room devices and the General
device alike:

- every entity suggests that ID before it is added (`with_roomcontrol_ids`).
  Home Assistant uses it for new entities and stores it in the entity
  registry, so its "recreate entity ID" button gives the roomcontrol_ ID too;
- entities registered before with an ID Home Assistant made itself are
  renamed once (`async_prefix_entity_ids`). An ID the user chose, or an
  entity the user gave its own name, is left alone.

Bundle lights choose their own ID (light.roomcontrol_<room>_<bundle>, see
light.py).
"""
from __future__ import annotations

from collections.abc import Iterable
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import UNDEFINED
from homeassistant.util import slugify

from .const import DOMAIN, GENERAL_DEVICE

_LOGGER = logging.getLogger(__name__)

PREFIX = f"{DOMAIN}_"
GENERAL_DEVICE_NAME = "Generiek"


def _device_name(hass: HomeAssistant, entity: Entity) -> str | None:
    """The name Home Assistant gives the entity's device."""
    info = entity.device_info or {}
    identifiers = info.get("identifiers") or set()
    if identifiers and (device := dr.async_get(hass).async_get_device(identifiers=identifiers)):
        return device.name_by_user or device.name
    if info.get("name"):
        return info["name"]
    ident = next((i for d, i in identifiers if d == DOMAIN), None)
    if ident == GENERAL_DEVICE:
        return GENERAL_DEVICE_NAME
    if ident and (area := ar.async_get(hass).async_get_area(ident)):
        return area.name
    return ident


def _suggest(hass: HomeAssistant, domain: str, entity: Entity) -> None:
    if entity.entity_id:
        return  # the entity chose its own ID (bundle lights)
    entity.hass = hass  # names may read the room config
    name = entity.name
    if name is UNDEFINED:
        name = None
    parts = [_device_name(hass, entity)] if entity.has_entity_name else []
    parts.append(name)
    object_id = slugify(" ".join(p for p in (DOMAIN, *parts) if p))
    if object_id and object_id != DOMAIN:
        entity.entity_id = f"{domain}.{object_id}"


def with_roomcontrol_ids(
    hass: HomeAssistant, domain: str, add: AddEntitiesCallback
) -> AddEntitiesCallback:
    """async_add_entities that first gives every entity its roomcontrol_ ID."""

    @callback
    def _add(entities: Iterable[Entity], update_before_add: bool = False, **kwargs: Any) -> None:
        entities = list(entities)
        for entity in entities:
            _suggest(hass, domain, entity)
        add(entities, update_before_add, **kwargs)

    return _add


def _made_by_ha(entry: er.RegistryEntry, device: dr.DeviceEntry | None, object_id: str) -> bool:
    """The current ID is one Home Assistant generated (device + entity name,
    possibly with _2, _3, …), not one the user typed."""
    devices = {n for n in ((device.name, device.name_by_user) if device else ()) if n}
    names = {n for n in (entry.original_name, entry.object_id_base) if n}
    autos = {slugify(d) for d in devices} | {slugify(f"{d} {n}") for d in devices for n in names}
    autos |= {slugify(n) for n in names}
    return any(
        a and (object_id == a or re.fullmatch(rf"{re.escape(a)}_\d+", object_id)) for a in autos
    )


@callback
def async_prefix_entity_ids(hass: HomeAssistant, config_entry_id: str) -> int:
    """Rename entities with an ID Home Assistant made to the ID its "recreate"
    would give now (roomcontrol_…); returns how many were renamed."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    renamed = 0
    for entry in list(er.async_entries_for_config_entry(ent_reg, config_entry_id)):
        object_id = entry.entity_id.split(".", 1)[1]
        if object_id.startswith(PREFIX) or entry.name:
            continue  # already prefixed, or the user named it
        if entry.domain == "light" and "_group_" in (entry.unique_id or ""):
            continue  # bundle lights: see light.py
        device = dev_reg.async_get(entry.device_id) if entry.device_id else None
        if not _made_by_ha(entry, device, object_id):
            continue  # chosen by the user: leave it
        wanted = ent_reg.async_regenerate_entity_id(entry)
        if wanted == entry.entity_id or not wanted.split(".", 1)[1].startswith(PREFIX):
            continue  # no roomcontrol_ suggestion stored (yet)
        _LOGGER.info("Renaming %s to %s", entry.entity_id, wanted)
        ent_reg.async_update_entity(entry.entity_id, new_entity_id=wanted)
        renamed += 1
    return renamed
