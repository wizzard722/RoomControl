import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.fan as FN
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls=[]
    for sv in ("turn_off","set_percentage"):
        async def h(c,sv=sv): calls.append((sv,dict(c.data)))
        hass.services.async_register("fan",sv,h)
    room={"area_id":"badkamer","fan_off_min":True}
    FN.stored_room=lambda h,a: room
    f=FN.RoomFan("badkamer"); f.hass=hass; f._members=["fan.mv"]
    await f.async_turn_off(); await f.async_set_percentage(0)
    room["fan_off_min"]=False; await f.async_turn_off()
    print([ (c[0], c[1].get("percentage")) for c in calls ])
    await hass.async_stop()
asyncio.run(main())
