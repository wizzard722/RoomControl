import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
import roomcontrol.energy as E
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize(); await hass.async_start()
    entry = config_entries.ConfigEntry(version=1, minor_version=1, domain="x", title="x", data={}, source="user", options={}, unique_id="x", discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    D, R = dr.async_get(hass), er.async_get(hass)
    d = D.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("x","plug")}, name="Truenas plug").id
    for oid in ("plug_a_unused","plug_power","plug_switch"):
        R.async_get_or_create("sensor" if oid!="plug_switch" else "switch","x",oid,suggested_object_id=oid,device_id=d,config_entry=entry)
    hass.states.async_set("sensor.plug_a_unused","unavailable",{"unit_of_measurement":"W"})
    hass.states.async_set("sensor.plug_power","42.5",{"unit_of_measurement":"W","device_class":"power"})
    print("picked:", E.auto_power_sensor(hass,"switch.plug_switch"))
    await hass.async_stop()
asyncio.run(main())
