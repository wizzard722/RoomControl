import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
import roomcontrol.energy as E
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize(); await hass.async_start()
    entry = config_entries.ConfigEntry(version=1, minor_version=1, domain="x", title="x", data={}, source="user", options={}, unique_id="x", discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    A, D, R = ar.async_get(hass), dr.async_get(hass), er.async_get(hass)
    bk = A.async_create("Bijkeuken"); other = A.async_create("Hal")
    def dev(n, area): d = D.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("x", n)}, name=n); D.async_update_device(d.id, area_id=area); return d.id
    wm, lampdev, haldev = dev("Wasmachine", bk.id), dev("Lamp", bk.id), dev("Halmeter", other.id)
    def ent(dom, oid, d): return R.async_get_or_create(dom, "x", oid, suggested_object_id=oid, device_id=d, config_entry=entry).entity_id
    ent("sensor","wm_power",wm); ent("sensor","wm_energy",wm); ent("sensor","wm_temp",wm)
    ent("light","bk_lamp",lampdev); ent("sensor","bk_lamp_power",lampdev)
    ent("sensor","hal_power",haldev)
    S = hass.states.async_set
    S("sensor.wm_power","1800",{"unit_of_measurement":"W"}); S("sensor.wm_energy","120.4",{"unit_of_measurement":"kWh"}); S("sensor.wm_temp","40",{"unit_of_measurement":"°C"})
    S("light.bk_lamp","on",{"brightness":255}); S("sensor.bk_lamp_power","9",{"unit_of_measurement":"W"}); S("sensor.hal_power","50",{"unit_of_measurement":"W"})
    room = {"area_id": bk.id, "groups": [{"id":"g","name":"Plafond","lights":["light.bk_lamp"]}]}
    parts = E.room_parts(hass, room)
    meters = [p for p in parts if p["kind"]=="meter"]
    check("one meter: the washing machine (lamp's device and other room excluded)", [(m["name"], m["sensor"], m["energy_sensor"], m["watts"], m["kwh"]) for m in meters], [("Wasmachine","sensor.wm_power","sensor.wm_energy",1800.0,120.4)])
    check("room total = lamp 9 W + meter 1800 W", round(sum(p["watts"] or 0 for p in parts),1), 1809.0)
    room["power"] = {meters[0]["key"]: {"hidden": True}}
    parts = E.room_parts(hass, room)
    check("hidden meter does not count", (round(sum(p["watts"] or 0 for p in parts),1), [p["hidden"] for p in parts if p["kind"]=="meter"]), (9.0, [True]))
    room["power"] = {meters[0]["key"]: {"sensor": "none"}}
    check("power cleared: meter unknown (not 0 W), no_power, energy kept", [(p["watts"], p["no_power"], p["energy_sensor"]) for p in E.room_parts(hass, room) if p["kind"]=="meter"], [(None, True, "sensor.wm_energy")])
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
