import asyncio, sys, tempfile, types
from datetime import datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
P = "alarm_control_panel.alarmo"
NIGHT = [{"name": "Nacht", "days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "23:30"}, "end": {"type": "time", "time": "06:30"}, "state": "armed_home"}]
async def run(home, alarm_at_end, cfg_extra=None):
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    for svc, st in A.SERVICE_FOR.items():
        async def h(c, st=svc): hass.states.async_set(P, st)
        hass.services.async_register("alarm_control_panel", st, h)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    hass.states.async_set("person.paul", "home" if home else "not_home")
    hass.data[DOMAIN] = {"settings": {"alarm_entity": P, "alarm": {"slots": NIGHT, **(cfg_extra or {})}}, "rooms": []}
    t = {"now": datetime(2026, 11, 20, 6, 0)}
    with patch.object(A.dt_util, "now", side_effect=lambda: t["now"]):
        hass.states.async_set(P, "disarmed")
        a = A.AlarmAutomation(hass); a.start(); await hass.async_block_till_done()
        hass.states.async_set(P, alarm_at_end); await hass.async_block_till_done()
        t["now"] = datetime(2026, 11, 20, 6, 31); a._tick(); await hass.async_block_till_done()
        result = hass.states.get(P).state
        a.stop()
    await hass.async_stop()
    return result
async def main():
    check("slot ends, someone home, Armed Home → Disarmed", await run(True, "armed_home"), "disarmed")
    check("slot ends, someone home, Armed Away set by hand → stays", await run(True, "armed_away"), "armed_away")
    check("slot ends, nobody home, near → Armed Away (since 2.2.0: Armed Home is only the night)", await run(False, "armed_home"), "armed_away")
    check("slot ends, nobody home, near = Armed Away → Armed Away", await run(False, "armed_home", {"near_state": "armed_away"}), "armed_away")
    check("'Change nothing' → stays", await run(True, "armed_home", {"outside": "none"}), "armed_home")
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
