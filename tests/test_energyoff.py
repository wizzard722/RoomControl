import asyncio, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN, energy_enabled
import roomcontrol.planner as PL
import roomcontrol.battery as B
import roomcontrol.energy as EN

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for s in ("turn_on", "turn_off"):
        async def h(c, s=s): calls.append((s, c.data["entity_id"])); hass.states.async_set(c.data["entity_id"], "on" if s == "turn_on" else "off")
        hass.services.async_register("switch", s, h)
    async def setv(c): calls.append(("set", c.data["value"]))
    hass.services.async_register("number", "set_value", setv)
    hass.states.async_set("switch.lader", "off")
    hass.data[DOMAIN] = {"settings": {}}
    check("default on", energy_enabled(hass), True)
    hass.data[DOMAIN]["settings"]["energy_enabled"] = False
    check("off", energy_enabled(hass), False)
    # planner: held the charger off → gives it back
    p = PL.Planner(hass)
    dev = {"key": "car", "kind": "car", "entity": "switch.lader", "kw": 3.7, "area": None, "name": "Auto"}
    p.plans = {"car": {"device": dev, "controllable": True, "mode_used": "cheap"}}; p._want = {"car": False}
    p._tick(); await hass.async_block_till_done()
    check("planner: charger back on, wants cleared", (calls, p._want), ([("turn_on", "switch.lader")], {}))
    calls.clear(); p._tick(); await hass.async_block_till_done()
    check("planner: nothing more", calls, [])
    # battery: back to own mode once
    hass.states.async_set("sensor.soc", "50"); hass.states.async_set("number.bat", "0")
    hass.data[DOMAIN]["settings"]["energy"] = {"battery": {"soc_sensor": "sensor.soc", "control": "number", "number_entity": "number.bat"}}
    hb = B.HomeBattery(hass); hb._sent = ("charge", 2000)
    hb._tick(); await hass.async_block_till_done(); hb._tick(); await hass.async_block_till_done()
    check("battery: own mode (0 W) once", calls, [("set", 0)])
    # energy: no tick work
    e = EN.Energy(hass)
    with patch.object(e, "status", side_effect=AssertionError("should not run")):
        e._tick()
    check("energy tick skipped", True, True)
    # back on: planner works again (no crash)
    hass.data[DOMAIN]["settings"]["energy_enabled"] = True
    check("on again", energy_enabled(hass), True)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
