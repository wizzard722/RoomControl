import asyncio, sys, tempfile, types
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
import roomcontrol.room_switches as RS
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for svc in ("turn_on", "turn_off"):
        async def h(c, s=svc):
            ids = c.data["entity_id"]; ids = [ids] if isinstance(ids, str) else ids
            calls.append((s, sorted(ids)))
            for i in ids: hass.states.async_set(i, "on" if s == "turn_on" else "off")
        hass.services.async_register("switch", svc, h)
    for i in ("switch.espresso", "switch.koelkast", "switch.tv", "switch.lamp"): hass.states.async_set(i, "on")
    hass.states.async_set("switch.tv", "off")
    P = "alarm_control_panel.x"; hass.states.async_set(P, "disarmed")
    hass.data[DOMAIN] = {"rooms": [{"area_id": "keuken", "switches": [
        {"entity_id": "switch.espresso"}, {"entity_id": "switch.koelkast", "may_off": False},
        {"entity_id": "switch.tv"}, {"entity_id": "switch.lamp", "off_on": ["all_off", "armed_away"]}]}],
        "settings": {"alarm_entity": P}}
    with patch.object(RS, "managed_areas", lambda h: {"keuken"}):
        check("all_off list", RS.switches_for(hass, "all_off", "keuken"), ["switch.espresso", "switch.tv", "switch.lamp"])
        check("old armed_away counts as nobody home", RS.switches_for(hass, "nobody_home"), ["switch.espresso", "switch.tv", "switch.lamp"])
        check("never off", RS.never_off(hass), {"switch.koelkast"})
        check("smoke excludes lamp (not chosen)", RS.switches_for(hass, "smoke"), ["switch.espresso", "switch.tv"])
        r = RS.RoomSwitches(hass); await r.async_load(); r.start()
        hass.states.async_set(P, "armed_away"); await hass.async_block_till_done()
        check("armed away: on ones off, fridge stays", (calls[-1], hass.states.get("switch.koelkast").state), (("turn_off", ["switch.espresso", "switch.lamp"]), "on"))
        hass.states.async_set(P, "armed_home"); await hass.async_block_till_done()
        check("armed home: back on, TV (was off) stays off", (calls[-1], hass.states.get("switch.tv").state), (("turn_on", ["switch.espresso", "switch.lamp"]), "off"))
        hass.states.async_set(P, "armed_away"); await hass.async_block_till_done(); hass.states.async_set(P, "disarmed"); await hass.async_block_till_done()
        check("disarmed: back on", calls[-1], ("turn_on", ["switch.espresso", "switch.lamp"]))
        await RS.async_switch_off(hass, ["switch.koelkast", "switch.espresso"], "test"); await hass.async_block_till_done()
        check("never-off never switched off", (hass.states.get("switch.koelkast").state, hass.states.get("switch.espresso").state), ("on", "off"))
        r.stop()
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
