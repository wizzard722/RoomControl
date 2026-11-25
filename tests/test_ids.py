import asyncio, logging, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_platform import EntityPlatform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.switch import SwitchEntity
from roomcontrol.entity_ids import with_roomcontrol_ids, async_prefix_entity_ids

class Sw(SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    def __init__(self, uid, ident, name, devname=None):
        self._attr_unique_id, self._attr_name = uid, name
        self._attr_device_info = DeviceInfo(identifiers={("roomcontrol", ident)}, **({"name": devname} if devname else {}))
    @property
    def is_on(self): return False

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = ConfigEntries(hass, {}); await hass.config_entries.async_initialize()
    entry = ConfigEntry(version=1, minor_version=1, domain="roomcontrol", title="RC", data={}, source="user",
                        options={}, unique_id=None, discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    area = ar.async_get(hass).async_create("Badkamer")
    entr = er.async_get(hass)
    # Existing entities from before: IDs made by Home Assistant, one chosen by the user.
    devr = dr.async_get(hass)
    room_dev = devr.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("roomcontrol", area.id)}, name="Badkamer")
    gen_dev = devr.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("roomcontrol", "general")}, name="Generiek")
    old = entr.async_get_or_create("switch", "roomcontrol", "rc_dim", config_entry=entry, device_id=room_dev.id,
                                   original_name="Dim", has_entity_name=True, object_id_base="Dim")
    user = entr.async_get_or_create("switch", "roomcontrol", "rc_announce", config_entry=entry, device_id=room_dev.id,
                                    original_name="Omroepen", has_entity_name=True, object_id_base="Omroepen")
    entr.async_update_entity(user.entity_id, new_entity_id="switch.mijn_omroep")
    print("before:", old.entity_id, "| user:", "switch.mijn_omroep")

    platform = EntityPlatform(hass=hass, logger=logging.getLogger("t"), domain="switch", platform_name="roomcontrol",
                              platform=None, scan_interval=timedelta(seconds=30), entity_namespace=None)
    platform.config_entry = entry
    add = with_roomcontrol_ids(hass, "switch", platform._async_schedule_add_entities_for_entry)
    add([Sw("rc_dim", area.id, "Dim"), Sw("rc_announce", area.id, "Omroepen"),
         Sw("rc_vacation", "general", "Vakantie", "Generiek"), Sw("rc_new", area.id, "Nieuw")])
    await asyncio.sleep(0.5)
    n = async_prefix_entity_ids(hass, entry.entry_id)
    await asyncio.sleep(0.3)
    got = {e.unique_id: e.entity_id for e in er.async_entries_for_config_entry(entr, entry.entry_id)}
    want = {"rc_dim": "switch.roomcontrol_badkamer_dim", "rc_announce": "switch.mijn_omroep",
            "rc_vacation": "switch.roomcontrol_generiek_vakantie", "rc_new": "switch.roomcontrol_badkamer_nieuw"}
    ok = True
    for k, w in want.items():
        g = got[k] == w; ok &= g; print("PASS" if g else "FAIL", k, got[k], "" if g else f"(want {w})")
    # Home Assistant's "recreate entity ID": what would it give?
    for uid in ("rc_dim", "rc_announce", "rc_vacation"):
        e = entr.async_get(got[uid]); print("recreate", uid, "->", entr.async_regenerate_entity_id(e))
    print("renamed:", n, "| second run:", async_prefix_entity_ids(hass, entry.entry_id))
    print("ALL PASS" if ok else "SOME FAILED")
    await hass.async_stop()
asyncio.run(main())
