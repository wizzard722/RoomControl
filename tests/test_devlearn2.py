import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
import roomcontrol.device_learning as D
import roomcontrol.rooms as R
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    S("switch.vaat","on"); S("sensor.vaat_w","1.2",{"unit_of_measurement":"W"})
    room={"area_id":"keuken","switches":[{"entity_id":"switch.vaat"}],"power":{"switch:switch.vaat":{"sensor":"sensor.vaat_w"}}}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{}}
    R.managed_areas=lambda h: {"keuken"}
    import roomcontrol.energy as E; E.managed_areas=lambda h: {"keuken"}
    dl=D.DeviceLearning(hass); await dl.async_load(); dl.start(); await hass.async_block_till_done()
    print("devices:", dl.sensors)
    for w in ("2100","2050","60","1.2"): S("sensor.vaat_w",w,{"unit_of_measurement":"W"}); await hass.async_block_till_done()
    p=dl.profiles("keuken"); print("profile:", {k:p[0][k] for k in ("name","standby","running","boot")} if p else None)
    dl.forget("keuken|switch:switch.vaat"); print("after forget runs:", dl.profiles("keuken")[0]["runs"])
    dl.shutdown(); await hass.async_stop()
asyncio.run(main())
