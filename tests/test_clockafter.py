import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.clocks import ClockManager
import roomcontrol.clocks as C
from roomcontrol.light import RoomControlLight
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    timers=[]
    C.async_call_later=lambda h, d, cb: (timers.append((d,cb)), lambda: None)[1]
    for case in ("nothing", "music_only"):
        hass.states.async_set("light.slk","off"); timers.clear()
        clock={"id":"w","time":"07:00","days":[0],"enabled":True,"bundles":["g1"],"stop_music": case=="music_only","stop_light":False}
        room={"area_id":"slk","alarm_clocks":[clock],"groups":[{"id":"g1","lights":["light.slk"]}],"motion_sensors":["binary_sensor.m"]}
        calls=[]
        class Light:
            def _dbg(self,*a,**k): pass
            async def async_call_lamps(self, svc, lamps, **k):
                calls.append(svc); [hass.states.async_set(x, "on" if svc=="turn_on" else "off") for x in lamps]
        hass.data[DOMAIN]={"rooms":[room],"settings":{},"entities":{"slk":Light()}}
        m=ClockManager(hass); m._persons_home=lambda r,c: True; m._music_start=lambda *a,**k: asyncio.sleep(0)
        m.states["slk:w"]=C.ClockState()
        await m._ring("slk:w",0)
        check(f"{case}: lamps ringing", m.lamps_ringing("slk"), {"light.slk"})
        check(f"{case}: stop step scheduled", len(timers), 1)
        await m.auto_stop("slk:w")
        check(f"{case}: after stop step, lamps released", m.lamps_ringing("slk"), set())
        m.states["slk:w"].cancel()
    # light: ended clock lamps follow grace period
    hass.states.async_set("light.slk","on"); hass.states.async_set("binary_sensor.m","off")
    ROOM={"area_id":"slk","motion_sensors":["binary_sensor.m"]}
    RoomControlLight._room=property(lambda self: ROOM); RoomControlLight._members=property(lambda self: ["light.slk"]); RoomControlLight._manual=property(lambda self: False)
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass; e._after_clock=set(); e._clock_prev={"light.slk"}
    e._clock_lamps=lambda: set(); e._dimmed_lamps=lambda: set(); e._dbg=lambda *a,**k: None; e.refresh_state=lambda: None
    e._on_by_motion=False; e._alarm_mode=lambda: "normal"; e._evening_lamps=lambda: []; e._lux_lamps_now=lambda: []
    e._motion_sensors=lambda: ["binary_sensor.m"]
    started=[]; e._check_idle=lambda: started.append(e._idle_lamps())
    e._on_clocks_updated()
    check("light: clock over → idle lamps (grace starts)", started, [["light.slk"]])
    e2=RoomControlLight.__new__(RoomControlLight); e2.__dict__.update(e.__dict__); e2._after_clock=set(); e2._clock_prev={"light.slk"}; e2._motion_sensors=lambda: []
    started.clear(); e2._check_idle=lambda: started.append(1); e2._on_clocks_updated()
    check("light: no motion sensor → stays on", (started, e2._after_clock), ([], set()))
    check("shutdown exists, stop(key) still async", (callable(getattr(ClockManager,"shutdown",None)), asyncio.iscoroutinefunction(ClockManager.stop)), (True, True))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
