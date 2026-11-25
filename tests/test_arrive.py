import asyncio, sys, tempfile, types
from datetime import datetime, timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
P = "alarm_control_panel.alarmo"
NIGHT = [{"name": "Nacht", "days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "22:00"}, "end": {"type": "time", "time": "06:30"}, "state": "armed_home"}]
async def run(dark=True, late_room=True, cfg=None, motion=False, slots=NIGHT, alarm="armed_home"):
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    calls = []
    for svc in A.SERVICE_FOR:
        async def h(c, st=svc): hass.states.async_set(P, st)
        hass.services.async_register("alarm_control_panel", A.SERVICE_FOR[svc], h)
    async def lon(c): calls.append(("on", c.data.get("entity_id"))); [hass.states.async_set(x, "on") for x in ([c.data["entity_id"]] if isinstance(c.data["entity_id"], str) else c.data["entity_id"])]
    async def loff(c): calls.append(("off", c.data.get("entity_id"))); [hass.states.async_set(x, "off") for x in ([c.data["entity_id"]] if isinstance(c.data["entity_id"], str) else c.data["entity_id"])]
    hass.services.async_register("light", "turn_on", lon); hass.services.async_register("light", "turn_off", loff)
    hass.states.async_set("sun.sun", "below_horizon" if dark else "above_horizon", {"elevation": -10 if dark else 20})
    hass.states.async_set("light.hal", "off"); hass.states.async_set("binary_sensor.m", "on" if motion else "off")
    hass.states.async_set("person.paul", "not_home")
    a = ar.async_get(hass).async_create("Hal")
    room = {"area_id": a.id, "lights": [{"entity_id": "light.hal"}], "late_home": late_room, "motion_sensors": ["binary_sensor.m"]}
    hass.data[DOMAIN] = {"rooms": [room], "entities": {}, "settings": {"alarm_entity": P, "alarm": {"slots": slots, **(cfg or {})}}}
    t = {"now": datetime(2026, 11, 20, 23, 0, tzinfo=dt_util.get_default_time_zone())}
    later = []
    def fake_later(h, delay, cb):
        later.append(cb); return lambda: later.remove(cb) if cb in later else None
    with patch.object(A.dt_util, "now", side_effect=lambda: t["now"]), patch.object(A, "async_call_later", fake_later):
        e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_hal"; e._members = ["light.hal"]
        await e.async_added_to_hass()
        hass.states.async_set(P, alarm)
        al = A.AlarmAutomation(hass); al.start(); await hass.async_block_till_done()
        hass.states.async_set("person.paul", "home"); await hass.async_block_till_done()
        r = {"state_after_arrive": hass.states.get(P).state, "lamp_after_arrive": hass.states.get("light.hal").state,
             "upcoming": [x["kind"] for x in al.upcoming()], "timer": al.status()["timer"]}
        for cb in list(later): cb(t["now"])
        await hass.async_block_till_done()
        r["state_end"] = hass.states.get(P).state; r["lamp_end"] = hass.states.get("light.hal").state
        r["log"] = [x["what"] for x in al.log]; r["timer_end"] = al.status()["timer"]
        al.stop()
    await hass.async_stop()
    return r
async def main():
    r = await run(); print(r)
    check("dark: disarmed on arrival", r["state_after_arrive"], "disarmed")
    check("dark: Later-thuis room lamp on", r["lamp_after_arrive"], "on")
    check("upcoming has lights off + rearm first", r["upcoming"][:2], ["arrive_lights_off", "rearm"]); t=r["timer"]; check("timer", (t["who"], t["lights"], t["state"], t["until"][11:16], t["from"][11:16]), ("person.paul", True, "armed_home", "23:10", "23:00")); check("timer gone after", r["timer_end"], None)
    check("after timer: lamp off", r["lamp_end"], "off")
    check("after timer: back to Armed Home", r["state_end"], "armed_home")
    r = await run(dark=False)
    check("light outside: lamp stays off", r["lamp_after_arrive"], "off")
    check("light outside: still rearms", r["state_end"], "armed_home")
    r = await run(late_room=False)
    check("room not set for Later thuis: lamp off", r["lamp_after_arrive"], "off")
    r = await run(cfg={"home_lights": False})
    check("option off: lamp off", r["lamp_after_arrive"], "off")
    r = await run(slots=[], alarm="armed_away")
    check("no slot, dark: lamp on", r["lamp_after_arrive"], "on")
    check("no slot: lamp off after timer", r["lamp_end"], "off")
    check("no slot: stays disarmed", r["state_end"], "disarmed")
    r = await run(motion=True)
    check("motion in the room at the end: lamp stays on", r["lamp_end"], "on")
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
