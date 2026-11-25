import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
import roomcontrol as RC
import roomcontrol.alarm_auto as A
from roomcontrol.switch import VacationSwitch, LeaveSwitch
from roomcontrol.slots import mode_slots
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    # 1 migration
    both={"days":[0],"start":{"type":"time","time":"18:00"},"end":{"type":"time","time":"23:00"},"holiday":"vacation"}
    data={"rooms":[{"area_id":"a","groups":[{"id":"g","slots":[{"holiday":"normal"},both]}],"motion_windows":{"binary_sensor.m":[{**both,"holiday":"only"}]},"locks":[{"entity_id":"lock.x","slots":[{"time":"22:00","holiday":"vacation"}]}]}],
          "settings":{"all_dim_slots":[both],"alarm":{"slots":[{**both,"state":"armed_home"}]}}}
    check("migration changed", RC._split_both_slots(data), True)
    g=data["rooms"][0]["groups"][0]["slots"]
    check("bundle slots split", [s.get("holiday") for s in g], ["normal","vacation_home","vacation_away"])
    check("motion/locks/alldim/alarm split", (len(data["rooms"][0]["motion_windows"]["binary_sensor.m"]), [s["holiday"] for s in data["rooms"][0]["locks"][0]["slots"]], len(data["settings"]["all_dim_slots"]), [s["state"] for s in data["settings"]["alarm"]["slots"]]),
          (2, ["vacation_home","vacation_away"], 2, ["armed_home","armed_home"]))
    check("second run: nothing", RC._split_both_slots(data), False)
    check("mode_slots verlof", [s["holiday"] for s in mode_slots(g,"home")], ["vacation_home"])
    # 2 switches + alarm
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set
    P="alarm_control_panel.a"
    sets=[]
    for st, svc in A.SERVICE_FOR.items():
        async def h(c, st=st): sets.append(st); S(P, st)
        hass.services.async_register("alarm_control_panel", svc, h)
    S(P,"disarmed"); S("person.p","home"); S("person.q","home")
    hass.data["roomcontrol"]={"rooms":[],"settings":{"alarm_entity":P,"persons":["person.p","person.q"],"alarm":{"distance_km":100}},"entities":{}}
    al=A.AlarmAutomation(hass); hass.data["roomcontrol"]["alarm"]=al
    vs=VacationSwitch(); vs.hass=hass; vs.entity_id="switch.vakantie"; ls=LeaveSwitch(); ls.hass=hass; ls.entity_id="switch.verlof"
    await vs.async_added_to_hass(); await ls.async_added_to_hass()
    await ls.async_turn_on(); check("verlof on", (ls.is_on, vs.is_on, hass.data["roomcontrol"]["vacation"]), (True, False, "home"))
    S(P,"armed_vacation"); await hass.async_block_till_done()
    check("alarm armed_vacation → vakantie on, verlof off", (vs.is_on, ls.is_on), (True, False))
    try:
        await ls.async_turn_on(); r="no error"
    except HomeAssistantError: r="refused"
    check("verlof refused during vakantie", r, "refused")
    S(P,"armed_away"); await hass.async_block_till_done()
    check("alarm leaves armed_vacation → vakantie off", vs.is_on, False)
    sets.clear(); await vs.async_turn_on(); await hass.async_block_till_done()
    check("vakantie by hand → alarm armed_vacation", (sets, vs.is_on), (["armed_vacation"], True))
    sets.clear(); await vs.async_turn_off(); await hass.async_block_till_done()
    check("vakantie off by hand, someone home → disarmed", (sets, vs.is_on), (["disarmed"], False))
    # 3 away target
    al.distance_km=lambda: 30.0; check("near → armed_away", al.away_target(), "armed_away")
    al.distance_km=lambda: 300.0; check("far → armed_vacation", al.away_target(), "armed_vacation")
    # crossing only
    al._away_active=True; al.all_away=lambda: True; S(P,"armed_vacation"); al._last_away_target="armed_away"
    al.distance_km=lambda: 30.0; sets.clear(); al._distance_changed(); await hass.async_block_till_done()
    check("no crossing (manual vakantie nearby) → stays", sets, [])
    al.distance_km=lambda: 300.0; al._distance_changed(); al.distance_km=lambda: 30.0; al._distance_changed(); await hass.async_block_till_done()
    check("crossing back within limit → armed_away", sets, ["armed_away"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
