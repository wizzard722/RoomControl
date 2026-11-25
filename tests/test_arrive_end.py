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
HELD=False
async def run(gap_minutes):
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    sets = []
    for svc in A.SERVICE_FOR:
        async def h(c, st=svc): sets.append(st); hass.states.async_set(P, st)
        hass.services.async_register("alarm_control_panel", A.SERVICE_FOR[svc], h)
    def onoff(state):
        async def f(c):
            ids = c.data["entity_id"]; [hass.states.async_set(x, state) for x in ([ids] if isinstance(ids, str) else ids)]
        return f
    hass.services.async_register("light", "turn_on", onoff("on")); hass.services.async_register("light", "turn_off", onoff("off"))
    notes = []
    async def pn(c): notes.append(c.data.get("message"))
    hass.services.async_register("persistent_notification", "create", pn)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    hass.states.async_set("light.hal", "off"); hass.states.async_set("binary_sensor.m", "off")
    hass.states.async_set("person.paul", "not_home", {"friendly_name": "Paul"}); hass.states.async_set("person.sarah", "not_home", {"friendly_name": "Sarah"})
    a = ar.async_get(hass).async_create("Hal")
    room = {"area_id": a.id, "lights": [{"entity_id": "light.hal"}], "late_home": True, "motion_sensors": ["binary_sensor.m"]}
    hass.data[DOMAIN] = {"rooms": [room], "entities": {}, "settings": {"alarm_entity": P, "alarm": {"slots": NIGHT}}}
    t = {"now": datetime(2026, 11, 20, 23, 0, tzinfo=dt_util.get_default_time_zone())}
    later = []
    def fake_later(h, delay, cb):
        later.append(cb); return lambda: later.remove(cb) if cb in later else None
    with patch.object(A.dt_util, "now", side_effect=lambda: t["now"]), patch.object(A, "async_call_later", fake_later):
        e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_hal"; e._members = ["light.hal"]
        await e.async_added_to_hass()
        if HELD: e._own_active = lambda: ["light.hal"]
        hass.states.async_set(P, "armed_home")
        al = A.AlarmAutomation(hass); al.start(); await hass.async_block_till_done()
        sets.clear()
        hass.states.async_set("person.paul", "home", {"friendly_name": "Paul"})
        if gap_minutes:
            await hass.async_block_till_done(); t["now"] += timedelta(minutes=gap_minutes)
        hass.states.async_set("person.sarah", "home", {"friendly_name": "Sarah"}); await hass.async_block_till_done()
        r = {"sets": list(sets), "timers": len(later), "timer": al.timer(), "lamp": hass.states.get("light.hal").state, "notes": list(notes)}
        for cb in list(later): cb(t["now"])
        await hass.async_block_till_done()
        r["arrive_after"] = set(hass.data[DOMAIN].get("arrive_active", set())); r["holds_after"] = e._late_home_holds()
        r["reasons"] = [x.get("reason") for x in e._debug if x.get("kind") == "on"]; r["log"]=[(x.get("kind"),x.get("reason"),x.get("why")) for x in e._debug if x.get("kind") in ("on","off","blocked")]
        r["end"] = hass.states.get(P).state; r["lamp_end"] = hass.states.get("light.hal").state; r["timer_end"] = al.timer()
        al.stop()
    await hass.async_stop()
    return r
async def main():
    global HELD
    for held in (False, True):
        HELD = held
        r = await run(0)
        check(f"held={held}: lamp on at arrival", r["lamp"], "on")
        check(f"held={held}: log says arrive, not late home", "arrive" in r["reasons"] and "late home" not in r["reasons"], True)
        check(f"held={held}: arrive ended after wait time", (r["arrive_after"], r["holds_after"]), (set(), False))
        print(r["log"]); check(f"held={held}: lamp after timer", r["lamp_end"], "off")
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
