import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
import roomcontrol.room_switches as RS
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    calls=[]
    for sv in ("turn_on","turn_off"):
        async def h(c,sv=sv):
            calls.append((sv,sorted(c.data["entity_id"])))
            for e in c.data["entity_id"]: hass.states.async_set(e,"on" if sv=="turn_on" else "off")
        hass.services.async_register("switch",sv,h)
    for e in ("switch.boiler","switch.koelkast","switch.tv"): hass.states.async_set(e,"on")
    RS.managed_areas=lambda h: {"keuken"}
    D=hass.data["roomcontrol"]={"settings":{},"rooms":[{"area_id":"keuken","switches":[
        {"entity_id":"switch.boiler","off_on":["vacation_away"]},
        {"entity_id":"switch.tv","off_on":["vacation_home","vacation_away","nobody_home"]},
        {"entity_id":"switch.koelkast","may_off":False,"off_on":["vacation_away"]}]}]}
    st=lambda: {e:hass.states.get(e).state for e in ("switch.boiler","switch.koelkast","switch.tv")}
    rs=RS.RoomSwitches(hass); await rs.async_load()
    D["vacation"]="away"; await rs.async_vacation(); await hass.async_block_till_done()
    check("elsewhere: boiler+tv off, koelkast (never) on", st(), {"switch.boiler":"off","switch.koelkast":"on","switch.tv":"off"})
    D["vacation"]="home"; await rs.async_vacation(); await hass.async_block_till_done()
    check("to at home: boiler back on, tv stays off", st(), {"switch.boiler":"on","switch.koelkast":"on","switch.tv":"off"})
    rs.nobody_home=lambda: True
    await rs.async_away("nobody home"); await hass.async_block_till_done()
    D["vacation"]=False; await rs.async_vacation(); await hass.async_block_till_done()
    check("vacation over while nobody home: tv stays off", st()["switch.tv"], "off")
    rs.nobody_home=lambda: False
    await rs.async_back("someone home"); await hass.async_block_till_done()
    check("someone home: tv back on", st()["switch.tv"], "on")
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
