from datetime import timedelta
import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
import roomcontrol.energy as E
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    ar.async_get(hass).async_create("Keuken"); ar.async_get(hass).async_create("Garage"); ar.async_get(hass).async_create("Zolder")
    keuken=ar.async_get(hass).async_get_area_by_name("Keuken").id; zolder=ar.async_get(hass).async_get_area_by_name("Zolder").id
    reg=er.async_get(hass)
    o=reg.async_get_or_create("sensor","x","oven_kw"); reg.async_update_entity(o.entity_id, area_id=keuken)
    w=reg.async_get_or_create("sensor","x","wasdroger"); reg.async_update_entity(w.entity_id, area_id=zolder)
    E.managed_areas=lambda h: {keuken,"garage",zolder}
    hass.data["roomcontrol"]={"rooms":[{"area_id":keuken,"phase":"L1"},{"area_id":zolder}],"settings":{"energy":{"phases":3,
       "phase_sensors":{"L1":"sensor.l1","L2":"sensor.l2","L3":"sensor.l3"},"charger_room":"garage","charger_phase":"L1","charge_from_kw":1.2,"plug_sensor":"binary_sensor.kabel"}}}
    en=E.Energy(hass)
    S("sensor.l1","2600",{"unit_of_measurement":"W"}); S("sensor.l2","2100",{"unit_of_measurement":"W"}); S("sensor.l3","200",{"unit_of_measurement":"W"})
    S(o.entity_id,"2.4",{"unit_of_measurement":"kW","friendly_name":"Oven"}); S(w.entity_id,"0",{"unit_of_measurement":"W"})
    S("binary_sensor.kabel","on")
    c=en.status()["car"]; check("oven in kW on L1 subtracted → not charging", (c["charging"], c["estimate_kw"]), (False, 0.2))
    # oven 2-phase not measured, laundry dryer in a room without phase on L1
    S(o.entity_id,"0",{"unit_of_measurement":"kW"}); S(w.entity_id,"2000",{"unit_of_measurement":"W"})
    S("sensor.l1","2300",{"unit_of_measurement":"W"}); S("sensor.l2","100",{"unit_of_measurement":"W"})
    c=en.status()["car"]; d=c["debug"]
    check("room without phase counted via total", (c["charging"], d["estimate_phase_kw"], d["estimate_total_kw"]), (False, 2.3, 0.6))
    check("debug lists it", d["rooms_no_phase"], [{"area": zolder, "watts": 2000.0}])
    # unmeasured oven, cable not connected
    S(w.entity_id,"0",{"unit_of_measurement":"W"}); S("sensor.l1","2600",{"unit_of_measurement":"W"}); S("sensor.l2","300",{"unit_of_measurement":"W"})
    S("binary_sensor.kabel","off")
    en._above_since=E.dt_util.utcnow()-timedelta(minutes=2); c=en.status()["car"]; check("unplugged → not charging", (c["charging"], c["why"]), (False,"unplugged"))
    S("binary_sensor.kabel","on")
    en._above_since=E.dt_util.utcnow()-timedelta(minutes=2); c=en.status()["car"]; check("plugged + 2.6 kW → charging", (c["charging"], c["why"]), (True,"power"))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
