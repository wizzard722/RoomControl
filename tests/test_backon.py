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
    hass.states.async_set("switch.koffie","on"); hass.states.async_set("switch.nas","on")
    RS.managed_areas=lambda h: {"keuken"}
    hass.data["roomcontrol"]={"settings":{},"rooms":[{"area_id":"keuken","switches":[{"entity_id":"switch.koffie"},{"entity_id":"switch.nas","back_on":False}]}]}
    rs=RS.RoomSwitches(hass); await rs.async_load()
    await rs.async_away("nobody home"); await hass.async_block_till_done()
    check("both off when nobody home", calls[-1], ("turn_off",["switch.koffie","switch.nas"]))
    await rs.async_back("someone home"); await hass.async_block_till_done()
    check("only koffie back on; nas stays off", (calls[-1], hass.states.get("switch.nas").state), (("turn_on",["switch.koffie"]),"off"))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
