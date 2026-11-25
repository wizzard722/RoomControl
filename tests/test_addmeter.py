import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
import roomcontrol.energy as E
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize(); await hass.async_start()
    S=hass.states.async_set
    A=ar.async_get(hass); keuken=A.async_create("Keuken").id; berging=A.async_create("Berging").id
    reg=er.async_get(hass); dreg=dr.async_get(hass)
    entry=ConfigEntry(version=1,minor_version=1,domain="x",title="x",data={},options={},source="user",unique_id=None,discovery_keys={},subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    dev=dreg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("x","oven")}, name="Oven meter")
    dreg.async_update_device(dev.id, area_id=berging)  # in another area
    w=reg.async_get_or_create("sensor","x","oven_w",device_id=dev.id); k=reg.async_get_or_create("sensor","x","oven_kwh",device_id=dev.id)
    S(w.entity_id,"2.3",{"unit_of_measurement":"kW","friendly_name":"Oven vermogen"}); S(k.entity_id,"120",{"unit_of_measurement":"kWh"})
    E.managed_areas=lambda h: {keuken,berging}
    rk={"area_id":keuken,"phase":"L1","power":{}}; rb={"area_id":berging,"phase":"L2"}
    hass.data["roomcontrol"]={"rooms":[rk,rb],"settings":{"energy":{"phases":3,"phase_sensors":{"L1":"sensor.l1"}}}}
    before_k=[p["key"] for p in E.room_parts(hass,rk)]; before_b=[(p["key"],p["watts"]) for p in E.room_parts(hass,rb)]
    check("without adding: not in kitchen", before_k, [])
    check("auto in berging (its area)", before_b, [(f"meter:{dev.id}", 2300.0)])
    rk["power"]={f"meter:{w.entity_id}":{"sensor":w.entity_id,"added":True}}
    pk=[(p["key"],p["watts"],p["added"],p["energy_sensor"]) for p in E.room_parts(hass,rk)]
    check("added in kitchen, kW→W, kWh found", pk, [(f"meter:{w.entity_id}",2300.0,True,k.entity_id)])
    check("no longer counted in berging", [p["key"] for p in E.room_parts(hass,rb)], [])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
