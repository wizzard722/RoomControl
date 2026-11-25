import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.vacuums as VM
from roomcontrol.switch import VacationSwitch
from roomcontrol.light import RoomControlLight
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set; P="alarm_control_panel.a"
    calls=[]
    for svc, st in (("alarm_disarm","disarmed"),("alarm_arm_away","armed_away"),("alarm_arm_vacation","armed_vacation"),("alarm_arm_home","armed_home")):
        async def h(c, st=st, svc=svc): calls.append(svc); S(P, st)
        hass.services.async_register("alarm_control_panel", svc, h)
    async def vstart(c): S("vacuum.r","cleaning")
    hass.services.async_register("vacuum","start",vstart)
    S("person.p","not_home"); S("vacuum.r","docked")
    room={"area_id":"hal","vacuums":["vacuum.r"]}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{"alarm_entity":P,"persons":["person.p"]}}
    VM.managed_areas=lambda h: {"hal"}
    vs=VacationSwitch(); vs.hass=hass; vs.entity_id="switch.vakantie"; await vs.async_added_to_hass()
    S(P,"armed_vacation"); await hass.async_block_till_done(); vs._apply_alarm_now()
    check("vakantie on", vs.is_on, True)
    m=VM.VacuumManager(hass); m.vacuum=lambda r: "vacuum.r"; m._rooms=lambda: [room]; m.sync=lambda *a: None
    await m.start_clean(area_id="hal"); await hass.async_block_till_done()
    check("disarmed for run, hold kept", (hass.states.get(P).state, hass.data["roomcontrol"].get("vacuum_alarm_hold")), ("disarmed","armed_vacation"))
    check("vakantie stays on during run", vs.is_on, True)
    RoomControlLight._room=property(lambda self: room)
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass; e._alarm_entity=lambda: P
    check("lamps see armed_vacation", e._alarm_state(), "armed_vacation")
    S("vacuum.r","docked"); await m._run_over("vacuum.r"); await hass.async_block_till_done()
    check("after run back to armed_vacation", (hass.states.get(P).state, "vacuum_alarm_hold" in hass.data["roomcontrol"], vs.is_on), ("armed_vacation", False, True))
    # someone comes home mid-run
    calls.clear(); await m.start_clean(area_id="hal"); await hass.async_block_till_done()
    S("person.p","home"); m._on_change(types.SimpleNamespace(data={"entity_id":"person.p","old_state":hass.states.get("vacuum.r"),"new_state":hass.states.get("person.p")})); await hass.async_block_till_done()
    check("hold cleared when someone home", ("vacuum_alarm_hold" in hass.data["roomcontrol"], e._alarm_state(), vs.is_on), (False, "disarmed", False))
    S("vacuum.r","docked"); await m._run_over("vacuum.r"); await hass.async_block_till_done()
    check("someone home: alarm stays disarmed", hass.states.get(P).state, "disarmed")
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
