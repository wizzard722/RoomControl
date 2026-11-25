import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from roomcontrol.const import DOMAIN
from roomcontrol.light import _rename_room_entity_ids
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    from homeassistant import config_entries as ce
    hass.config_entries = ce.ConfigEntries(hass, {}); await hass.config_entries.async_initialize()
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    import inspect
    kw = dict(domain=DOMAIN, title="RoomControl", data={}, source="user", version=2, minor_version=1, options={}, unique_id=DOMAIN)
    params = inspect.signature(ConfigEntry).parameters
    if "discovery_keys" in params: kw["discovery_keys"] = {}
    if "subentries_data" in params: kw["subentries_data"] = None
    entry = ConfigEntry(**kw)
    hass.config_entries._entries[entry.entry_id] = entry
    dev = dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={(DOMAIN, "slk")}, name="Slaapkamer")
    reg = er.async_get(hass)
    mk = lambda dom, uid, oid: reg.async_get_or_create(dom, DOMAIN, uid, suggested_object_id=oid, config_entry=entry, device_id=dev.id)
    mk("light", "u1", "roomcontrol_slaapkamer"); mk("light", "u2", "roomcontrol_slaapkamer_plafond"); mk("sensor", "u3", "roomcontrol_slaapkamer_gordijnen_status"); mk("switch", "u4", "mijn_eigen_naam"); mk("light", "u5", "roomcontrol_slaapkamer_2_test")
    _rename_room_entity_ids(hass, entry.entry_id, dev.id, "Slaapkamer", "Grote slaapkamer")
    ids = sorted(e.entity_id for e in er.async_entries_for_device(reg, dev.id))
    check("renamed", ids, sorted(["light.roomcontrol_grote_slaapkamer", "light.roomcontrol_grote_slaapkamer_plafond", "sensor.roomcontrol_grote_slaapkamer_gordijnen_status", "switch.mijn_eigen_naam", "light.roomcontrol_grote_slaapkamer_2_test"]))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
