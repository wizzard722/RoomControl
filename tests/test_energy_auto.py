import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
import roomcontrol.energy as E
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize(); await hass.async_start()
    entry = config_entries.ConfigEntry(version=1, minor_version=1, domain="shelly", title="x", data={}, source="user", options={}, unique_id="x", discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    D, R = dr.async_get(hass), er.async_get(hass)
    def dev(n): return D.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("shelly", n)}, name=n).id
    d1, d2, d3 = dev("spot1"), dev("spot2"), dev("plug")
    def ent(dom, oid, d): return R.async_get_or_create(dom, "shelly", oid, suggested_object_id=oid, device_id=d, config_entry=entry).entity_id
    ent("light","spot1",d1); ent("sensor","spot1_power",d1); ent("sensor","spot1_energy",d1)
    ent("light","spot2",d2); ent("sensor","spot2_power_kw",d2)
    ent("switch","koffie",d3); ent("sensor","koffie_power",d3); ent("sensor","koffie_energy",d3)
    S = hass.states.async_set
    S("light.spot1","on"); S("light.spot2","on"); S("switch.koffie","on")
    S("sensor.spot1_power","7",{"unit_of_measurement":"W"}); S("sensor.spot1_energy","3",{"unit_of_measurement":"kWh"})
    S("sensor.spot2_power_kw","0.01",{"unit_of_measurement":"kW"}); S("sensor.koffie_power","900",{"unit_of_measurement":"W"}); S("sensor.koffie_energy","12.5",{"unit_of_measurement":"kWh"})
    check("auto: W sensor on lamp's device", E.auto_power_sensor(hass, "light.spot1"), "sensor.spot1_power")
    check("auto: kW sensor not used (only W)", E.auto_power_sensor(hass, "light.spot2"), None)
    room = {"area_id":"k","groups":[{"id":"g","name":"Spots","lights":["light.spot1","light.spot2"]}],"switches":[{"entity_id":"switch.koffie"}]}
    parts = E.room_parts(hass, room)
    check("bundle auto: spot1 sensor, source sensor", (parts[0]["watts"], parts[0]["source"], parts[0]["auto"], parts[0]["sensors"]), (7.0, "sensor", True, {"light.spot1":"sensor.spot1_power"}))
    check("switch auto", (parts[1]["watts"], parts[1]["auto"]), (900.0, True))
    check("energy auto: spot1 kWh sensor", (parts[0]["energy"], parts[0]["kwh"]), ({"light.spot1":"sensor.spot1_energy"}, 3.0))
    check("energy auto: switch kWh", (parts[1]["energy"], parts[1]["kwh"]), ({"switch.koffie":"sensor.koffie_energy"}, 12.5))
    room["power"] = {"switch:switch.koffie":{"energy":{"switch.koffie":"none"}}}
    check("energy cleared by user", E.room_parts(hass, room)[1]["energy"], {})
    room["power"] = {"bundle:g":{"mode":"sensor","sensors":{"light.spot1":"none"}}, "switch:switch.koffie":{"watts":1200}}
    parts = E.room_parts(hass, room)
    check("user said none for spot1 → no sensor; falls back to fixed 0", (parts[0]["source"], parts[0]["watts"]), ("watts", 0.0))
    check("user chose fixed for switch → wins over auto", (parts[1]["source"], parts[1]["watts"], parts[1]["auto"]), ("watts", 1200.0, False))
    room["power"] = {"bundle:g":{"watts":40}}
    check("user chose fixed for bundle → wins", E.room_parts(hass, room)[0]["source"], "watts")
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
