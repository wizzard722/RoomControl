import asyncio, sys, tempfile, types
from datetime import datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from roomcontrol.const import DOMAIN, SIGNAL_CONFIG_UPDATED
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
P = "alarm_control_panel.alarmo"
async def setup(start_hass):
    hass = HomeAssistant(tempfile.mkdtemp())
    if start_hass: await hass.async_start()
    for svc, st in A.SERVICE_FOR.items():
        async def h(c, st=svc): hass.states.async_set(P, st)
        hass.services.async_register("alarm_control_panel", st, h)
    hass.states.async_set(P, "disarmed"); hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    hass.states.async_set("person.paul", "home")
    hass.data[DOMAIN] = {"settings": {"alarm_entity": P, "alarm": {}}, "rooms": []}
    return hass
NIGHT = [{"name": "Nacht", "days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "23:30"}, "end": {"type": "time", "time": "06:30"}, "state": "armed_home"}]
async def main():
    with patch.object(A.dt_util, "now", return_value=datetime(2026, 11, 19, 23, 45)):
        hass = await setup(True)
        a = A.AlarmAutomation(hass); a.start(); await hass.async_block_till_done()
        check("no slots yet: disarmed", hass.states.get(P).state, "disarmed")
        hass.data[DOMAIN]["settings"]["alarm"] = {"slots": NIGHT}; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
        check("slot configured while it runs: Armed Home at once", hass.states.get(P).state, "armed_home")
        hass.states.async_set(P, "disarmed"); await hass.async_block_till_done()
        hass.data[DOMAIN]["settings"]["alarm"] = {"slots": NIGHT, "notify": "notify.x"}; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
        check("disarmed by hand, other setting changed: stays disarmed", hass.states.get(P).state, "disarmed")
        hass.data[DOMAIN]["settings"]["alarm"] = {"slots": [{**NIGHT[0], "state": "armed_night"}], "notify": "notify.x"}; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
        check("slot changed: its new state at once", hass.states.get(P).state, "armed_night")
        a.stop(); await hass.async_stop()
        # startup during a slot
        hass = await setup(False); hass.data[DOMAIN]["settings"]["alarm"] = {"slots": NIGHT}
        a = A.AlarmAutomation(hass); a.start(); await hass.async_block_till_done()
        check("before HA has started: nothing yet", hass.states.get(P).state, "disarmed")
        await hass.async_start(); await hass.async_block_till_done()
        check("HA started during the slot: Armed Home", hass.states.get(P).state, "armed_home")
        a.stop(); await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
