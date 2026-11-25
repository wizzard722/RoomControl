import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.light import RoomControlLight
import roomcontrol.vacuums as VM
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set; P="alarm_control_panel.a"
    ROOM={"away_replay":True,"covers_open_at":"time","covers_open_time":"07:00"}
    RoomControlLight._room=property(lambda self: ROOM); RoomControlLight._members=property(lambda self: ["light.a","light.b"]); RoomControlLight._manual=property(lambda self: False)
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass; e.entity_id="light.rc"
    e._sun_down=lambda: True; e._alarm_entity=lambda: P
    S("person.p","not_home"); hass.data["roomcontrol"]={"settings":{"persons":["person.p"]}}
    for st, want in (("armed_away",True),("armed_vacation",True),("armed_home",False),("disarmed",False)):
        S(P,st); check(f"replay active at {st}", e._replay_active(), want)
    e._alarm_entity=lambda: None
    check("no alarm, nobody home → active", e._replay_active(), True)
    S("person.p","home"); check("no alarm, someone home → not", e._replay_active(), False)
    # end: off except held
    S("light.a","on"); S("light.b","on")
    calls=[]
    async def call(svc, lamps=None, **k): calls.append((svc, lamps))
    e._async_call=call; e._dbg=lambda *a,**k: None; e._learn=lambda: object()
    e._replay_on={"light.a","light.b"}; e._evening_lamps=lambda: ["light.b"]; e._lux_lamps_now=lambda: []; e._late_home_holds=lambda: False
    e._replay_step(); await hass.async_block_till_done()
    check("replay ends: off except slot-held lamp", (calls, e._replay_on), ([("turn_off",["light.a"])], set()))
    # covers open time mode
    hass.data["roomcontrol"]["vacation"]=False; check("covers time normal", e._covers_open_at(), ("time", 420))
    ROOM["covers_open_vacation"]=["normal"]; hass.data["roomcontrol"]["vacation"]="away"
    check("covers time skipped on vakantie → open when light", e._covers_open_at(), None)
    # vacuum skip
    m=VM.VacuumManager(hass); plan={"id":"p","time":"10:00","days":[0],"enabled":True,"vacation":["normal"]}
    m.find=lambda k: ("a",{},plan); st=VM.PlanState() if hasattr(VM,"PlanState") else None; m.states={"a:p":st}
    m._schedule_next=lambda *a: None; started=[]
    async def sc(k): started.append(k)
    m.start_clean=sc
    await m._moment("a:p"); check("vacuum skipped on vakantie", (started, st.last_note), ([], "skip_away"))
    hass.data["roomcontrol"]["vacation"]=False; m.blocked=lambda p: None
    await m._moment("a:p"); check("vacuum runs normally", started, ["a:p"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
