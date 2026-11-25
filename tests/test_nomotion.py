import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol as RC
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    forgot=[]
    class L:
        def forget(self,a,w): forgot.append((a,w))
    class St:
        async def async_save(self,d): pass
    hass.data["roomcontrol"]={"rooms":[{"area_id":"hal","motion_sensors":["binary_sensor.pir"],"adaptive_grace":True},{"area_id":"keuken","motion_sensors":["binary_sensor.a","binary_sensor.b"],"adaptive_grace":True}],"settings":{},"store":St(),"learn":L()}
    await RC._async_save(hass, rooms=[{"area_id":"hal","motion_sensors":[],"adaptive_grace":True},{"area_id":"keuken","motion_sensors":["binary_sensor.a"],"adaptive_grace":True}])
    r=hass.data["roomcontrol"]["rooms"]
    print("hal grace off:", "adaptive_grace" not in r[0], "| keuken keeps:", r[1].get("adaptive_grace"), "| forgotten:", forgot)
    await hass.async_stop()
asyncio.run(main())
