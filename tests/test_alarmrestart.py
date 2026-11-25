import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"persons": [], "alarm_entity": "alarm_control_panel.alarmo", "alarm": {}}, "rooms": []}
    a = A.AlarmAutomation(hass)
    runs = []
    a._on_alarm = lambda new, old: runs.append((old, new))
    a.panel = lambda: "alarm_control_panel.alarmo"
    class Ev:
        def __init__(s, old, new): s.data={"entity_id":"alarm_control_panel.alarmo","old_state":old and State("alarm_control_panel.alarmo",old),"new_state":State("alarm_control_panel.alarmo",new)}
    for old, new in [(None,"disarmed"),("unavailable","disarmed"),("unknown","armed_away")]:
        a._on_change(Ev(old,new))
    check("start-up / reload: no state actions", runs, [])
    a._on_change(Ev("disarmed","armed_home")); a._on_change(Ev("armed_home","disarmed"))
    check("real changes still run", runs, [("disarmed","armed_home"),("armed_home","disarmed")])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
