import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for mod in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[mod] = types.ModuleType(mod)
from homeassistant.core import HomeAssistant, ServiceCall
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight, async_load_fans_applied, keep_fans_applied
from roomcontrol.fan_activity import fan_activities
import roomcontrol.light as L
L.anyone_home=lambda h: True
def make(hass, room):
    e = RoomControlLight.__new__(RoomControlLight)
    e.hass, e._area_id, e._fan_key, e._fan_temp_pct, e._manual_until = hass, room["area_id"], None, None, None
    e.entity_id = None
    hass.data[DOMAIN]["entities"][room["area_id"]] = e
    return e
async def main():
    d=tempfile.mkdtemp()
    room={"area_id":"badkamer","motion_sensors":["binary_sensor.pir"],"fans":["fan.mv"],"fan_steps":[{"minutes":0,"percentage":40}],"fan_run_on":1}
    # first run: RoomControl switches the fan on, then "restart"
    hass = HomeAssistant(d); await hass.async_start()
    calls=[]
    async def rec(c: ServiceCall): calls.append((c.service, c.data.get("percentage")))
    for sv in ("set_percentage","turn_off"): hass.services.async_register("fan",sv,rec)
    hass.data[DOMAIN]={"rooms":[room],"settings":{},"entities":{}}
    await async_load_fans_applied(hass)
    e=make(hass,room)
    hass.states.async_set("binary_sensor.pir","on"); e._fan_update(); await asyncio.sleep(0.2)
    print("first run:", calls, "| remembered:", hass.data[DOMAIN]["fan_applied"])
    await hass.async_block_till_done(); await hass.data[DOMAIN]["fan_store"]._async_handle_write_data() if hasattr(hass.data[DOMAIN]["fan_store"],"_async_handle_write_data") else None
    await hass.async_stop(force=True)
    # second run after restart: fan still on, no motion
    hass2 = HomeAssistant(d); await hass2.async_start()
    calls.clear()
    for sv in ("set_percentage","turn_off"): hass2.services.async_register("fan",sv,rec)
    hass2.data[DOMAIN]={"rooms":[room],"settings":{},"entities":{}}
    await async_load_fans_applied(hass2)
    print("restored:", hass2.data[DOMAIN]["fan_restored"])
    hass2.states.async_set("fan.mv","on",{"percentage":40}); hass2.states.async_set("binary_sensor.pir","off")
    e2=make(hass2,room)
    e2._fan_update(); await asyncio.sleep(1.6); await hass2.async_block_till_done()
    print("after restart + run-on:", calls, "| activity left:", bool(fan_activities(hass2)))
    await hass2.async_stop(force=True)
asyncio.run(main())
