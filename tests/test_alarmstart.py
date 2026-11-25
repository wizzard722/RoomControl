import asyncio, sys, tempfile, types
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant, State
from roomcontrol.const import DOMAIN
import roomcontrol.switch as S

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

class Room:
    def __init__(s): s.dimmed = False
    async def async_set_dim(s, d, by_alarm=False): s.dimmed = d

async def run(hass, restored_on, restored_inside, last_alarm, alarm_now, inside, follows=True, dimmed=False):
    hass.data[DOMAIN]["settings"] = {"alarm_entity": "alarm_control_panel.h", "all_dim_follows_alarm": follows}
    hass.states.async_set("alarm_control_panel.h", alarm_now)
    sw = S.AllDimSwitch.__new__(S.AllDimSwitch); sw.hass = hass; sw.entity_id = None
    rooms = [Room(), Room()]
    for r in rooms: r.dimmed = dimmed
    sw._room_lights = lambda: rooms
    sw._restored_on, sw._restored_inside, sw._last_alarm = restored_on, restored_inside, last_alarm
    sw._watching, sw._unsub, sw._in_window, sw._started = [], None, None, False
    sw._refresh = lambda *a: None
    with patch.object(S, "all_dim_active", return_value=inside):
        sw._startup(); await hass.async_block_till_done()
    return all(r.dimmed for r in rooms), sw

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.data[DOMAIN] = {}
    # follows the alarm: its state at startup decides
    check("start armed home, was off: on", (await run(hass, False, False, "disarmed", "armed_home", False))[0], True)
    check("start disarmed, was on in slot: off", (await run(hass, True, True, "disarmed", "disarmed", True))[0], False)
    check("start armed away: restored on stays", (await run(hass, True, False, "armed_home", "armed_away", False))[0], True)
    check("start armed away: restored off stays", (await run(hass, False, False, "armed_home", "armed_away", False))[0], False)
    # not following the alarm: as before the restart / time slots
    check("not following: restored on", (await run(hass, True, True, "armed_home", "disarmed", True, follows=False))[0], True)
    check("not following: slot ended while down", (await run(hass, True, True, "disarmed", "disarmed", False, follows=False))[0], False)
    check("not following: slot started while down", (await run(hass, False, False, "disarmed", "disarmed", True, follows=False))[0], True)
    check("not following: first run in slot", (await run(hass, None, None, None, "disarmed", True, follows=False))[0], True)
    # while running
    on, sw = await run(hass, False, False, "disarmed", "disarmed", False)
    calls = []
    async def fake_set(d): calls.append(d)
    sw._set = fake_set
    ev = lambda new, old: types.SimpleNamespace(data={"new_state": State("alarm_control_panel.h", new), "old_state": State("alarm_control_panel.h", old)})
    sw._on_alarm(ev("arming", "disarmed")); sw._on_alarm(ev("armed_home", "arming")); await hass.async_block_till_done()
    check("armed home while running: all dim on", calls, [True])
    for r in sw._room_lights(): r.dimmed = True
    calls.clear(); sw._on_alarm(ev("disarmed", "armed_home")); await hass.async_block_till_done()
    check("disarmed while running: all dim off", calls, [False])
    # alarm unknown at startup, then known
    on, sw = await run(hass, False, False, "armed_home", "unavailable", False)
    check("alarm unknown at startup: restored off", on, False)
    calls.clear(); sw._set = fake_set
    sw._on_alarm(ev("armed_home", "unavailable")); await hass.async_block_till_done()
    check("then armed home appears (same as before restart): still applied", calls, [True])
    # Vacation
    hass.data[DOMAIN]["settings"] = {"alarm_entity": "alarm_control_panel.h", "vacation_follows_alarm": True}
    # Since 2.2.0: Vakantie = "away" and follows Armed Vacation; Verlof ("home") is never touched by the alarm.
    v = S.VacationSwitch.__new__(S.VacationSwitch); v.hass = hass; v.entity_id = None; hass.data[DOMAIN]["vacation"] = "away"
    hass.states.async_set("alarm_control_panel.h", "disarmed"); v._apply_alarm_now()
    check("Vakantie on, alarm disarmed at start: off", hass.data[DOMAIN]["vacation"], False)
    hass.data[DOMAIN]["vacation"] = "home"; v._apply_alarm_now()
    check("Verlof on, alarm disarmed: stays", hass.data[DOMAIN]["vacation"], "home")
    hass.data[DOMAIN]["vacation"] = False; hass.states.async_set("alarm_control_panel.h", "armed_vacation"); v._apply_alarm_now()
    check("armed vacation at start: Vakantie on", (hass.data[DOMAIN]["vacation"], v.is_on), ("away", True))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
