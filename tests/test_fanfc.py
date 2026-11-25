import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for mod in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[mod] = types.ModuleType(mod)
from homeassistant.core import HomeAssistant, ServiceCall
from roomcontrol.const import DOMAIN
import roomcontrol.light as L
from roomcontrol.light import RoomControlLight
L.anyone_home=lambda h: True
L.FAN_CONTROL_GRACE=0.2
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls=[]
    async def rec(c: ServiceCall):
        calls.append((c.service, c.data.get("percentage")))
        for f in c.data["entity_id"]:
            hass.states.async_set(f, "off" if c.service=="turn_off" else "on", {"percentage": 0 if c.service=="turn_off" else c.data.get("percentage")})
    for sv in ("set_percentage","turn_off"): hass.services.async_register("fan",sv,rec)
    room={"area_id":"badkamer","motion_sensors":["binary_sensor.pir"],"fans":["fan.mv"],"fan_steps":[{"minutes":0,"percentage":40}],"fan_run_on":60,"full_control":True}
    hass.data[DOMAIN]={"rooms":[room],"settings":{},"entities":{}}
    e = RoomControlLight.__new__(RoomControlLight)
    e.hass, e._area_id, e._fan_key, e._fan_temp_pct, e._manual_until = hass, "badkamer", None, None, None
    e.entity_id=None; e._tracks={}; e._debug=[]
    e._dbg=lambda *a, **k: None
    hass.data[DOMAIN]["entities"]["badkamer"]=e
    hass.states.async_set("fan.mv","off",{"percentage":0}); hass.states.async_set("binary_sensor.pir","off")
    e._setup_fan_control()
    hass.states.async_set("fan.mv","on",{"percentage":100}); await asyncio.sleep(0.6); await hass.async_block_till_done()
    check("on by hand while it should be off → off", (calls[-1:], hass.states.get("fan.mv").state), ([("turn_off",None)],"off"))
    calls.clear(); hass.states.async_set("binary_sensor.pir","on"); e._fan_update(); await asyncio.sleep(0.3); await hass.async_block_till_done()
    check("motion → 40%", calls, [("set_percentage",40)])
    await asyncio.sleep(0.3); calls.clear()
    hass.states.async_set("fan.mv","on",{"percentage":100}); await asyncio.sleep(0.6); await hass.async_block_till_done()
    check("set to 100% by hand during activity → back to 40%", calls, [("set_percentage",40)])
    calls.clear(); room["fan_off_min"]=True; hass.states.async_set("binary_sensor.pir","off")
    from roomcontrol.fan_activity import fan_activities
    e._fan_end(("fan.mv",)); await asyncio.sleep(0.4); await hass.async_block_till_done()
    hass.states.async_set("fan.mv","off",{"percentage":0}); await asyncio.sleep(0.6); await hass.async_block_till_done()
    check("off = 1%: switched off by hand → back to 1%", calls[-1:], [("set_percentage",1)])
    calls.clear(); room["full_control"]=False; e._setup_fan_control()
    hass.states.async_set("fan.mv","on",{"percentage":100}); await asyncio.sleep(0.6); await hass.async_block_till_done()
    check("option off → left alone", calls, [])
    await hass.async_stop(force=True); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
