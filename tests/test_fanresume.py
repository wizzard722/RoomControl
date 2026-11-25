import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for mod in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[mod] = types.ModuleType(mod)
from homeassistant.core import HomeAssistant, ServiceCall
from roomcontrol.const import DOMAIN
import roomcontrol.light as L
from roomcontrol.light import RoomControlLight, async_load_fans_applied
from roomcontrol.fan_activity import fan_activities
L.anyone_home=lambda h: True
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
STEP=0.02  # minutes (1.2 s)
room={"area_id":"badkamer","motion_sensors":["binary_sensor.pir"],"fans":["fan.mv"],
      "fan_steps":[{"minutes":0,"percentage":33},{"minutes":STEP,"percentage":66},{"minutes":3*STEP,"percentage":100}],"fan_run_on":3}
def make(hass):
    e = RoomControlLight.__new__(RoomControlLight)
    e.hass, e._area_id, e._fan_key, e._fan_temp_pct, e._manual_until = hass, "badkamer", None, None, None
    e.entity_id=None; e._tracks={}
    hass.data[DOMAIN]["entities"]["badkamer"]=e
    return e
async def run(d, pre, body):
    hass = HomeAssistant(d); await hass.async_start()
    calls=[]
    async def rec(c: ServiceCall):
        calls.append((c.service, c.data.get("percentage")))
        for f in c.data["entity_id"]:
            hass.states.async_set(f, "off" if c.service=="turn_off" else "on", {"percentage": 0 if c.service=="turn_off" else c.data.get("percentage")})
    for sv in ("set_percentage","turn_off"): hass.services.async_register("fan",sv,rec)
    hass.data[DOMAIN]={"rooms":[room],"settings":{},"entities":{}}
    await async_load_fans_applied(hass)
    pre(hass)
    e=make(hass)
    r=await body(hass,e,calls)
    await hass.data[DOMAIN]["fan_store"].async_save(hass.data[DOMAIN]["fan_store"]._data["data"]) if getattr(hass.data[DOMAIN]["fan_store"],"_data",None) and isinstance(hass.data[DOMAIN]["fan_store"]._data,dict) and "data" in hass.data[DOMAIN]["fan_store"]._data else None
    await hass.async_stop(force=True)
    return r
async def main():
    d=tempfile.mkdtemp()
    async def first(hass,e,calls):
        hass.states.async_set("binary_sensor.pir","on"); e._fan_update(); await asyncio.sleep(1.6); await hass.async_block_till_done()
        a=fan_activities(hass)[("fan.mv",)]; return (a.step, a.pct, list(calls))
    r=await run(d, lambda h: None, first)
    check("before restart: step 2 at 66%", r[:2], (2,66))
    # restart with motion: continues to step 3 (not back to step 1)
    async def second(hass,e,calls):
        hass.states.async_set("binary_sensor.pir","on")
        e._fan_update(); a=fan_activities(hass)[("fan.mv",)]; resumed=(a.step,a.pct)
        await asyncio.sleep(2.6); await hass.async_block_till_done()
        return resumed, fan_activities(hass)[("fan.mv",)].step, calls
    r=await run(d, lambda h: h.states.async_set("fan.mv","on",{"percentage":66}), second)
    check("after restart: resumed at step 2 / 66%", r[0], (2,66))
    check("then step 3 at 100% (no restart from step 1)", (r[1], r[2]), (3,[("set_percentage",100)]))
    # restart during run-on: remaining time kept, then off
    async def third(hass,e,calls):
        hass.states.async_set("binary_sensor.pir","off"); e._fan_update()
        a=fan_activities(hass)[("fan.mv",)]; return a.off_at is not None
    await run(d, lambda h: h.states.async_set("fan.mv","on",{"percentage":100}), third)
    async def fourth(hass,e,calls):
        hass.states.async_set("binary_sensor.pir","off"); e._fan_update()
        a=fan_activities(hass)[("fan.mv",)]; left=(a.off_at-L.dt_util.utcnow()).total_seconds()
        early=list(calls)
        await asyncio.sleep(6); await hass.async_block_till_done()
        return round(left), early, calls, bool(fan_activities(hass))
    r=await run(d, lambda h: h.states.async_set("fan.mv","on",{"percentage":100}), fourth)
    check("restart during run-on: rest of the run-on first (still on right after start), then off", (r[0] in (4,5), r[1], r[2], r[3]), (True,[],[("turn_off",None)],False))
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
