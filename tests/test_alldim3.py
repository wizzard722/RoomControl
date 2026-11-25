import asyncio, sys, tempfile, types
from datetime import datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
import roomcontrol.switch as SW

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    for s in ("turn_on", "turn_off"):
        async def rec(c): pass
        hass.services.async_register("light", s, rec)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    rooms, ents = [], {}
    for name, lamp, dim in (("Woonkamer", "light.wk", True), ("Garage", "light.ga", False)):
        a = ar.async_get(hass).async_create(name)
        hass.states.async_set(lamp, "on", {"brightness": 200})
        rooms.append({"area_id": a.id, "lights": [{"entity_id": lamp}], "groups": [{"id": "g1", "lights": [lamp], "dim": dim}]})
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {"all_dim_slots": [{"days":[0,1,2,3,4,5,6],"start":{"type":"time","time":"23:00"},"end":{"type":"time","time":"07:00"}},{"days":[2],"start":{"type":"time","time":"13:00"},"end":{"type":"time","time":"14:00"}}]}, "entities": {}}
    for r, lamp in zip(rooms, ("light.wk", "light.ga")):
        e = RoomControlLight(hass, r["area_id"]); e.hass = hass; e.entity_id = f"light.rc_{lamp[6:]}"
        e._members = [lamp]; await e.async_added_to_hass(); ents[r["area_id"]] = e
    wk, ga = ents["woonkamer"], ents["garage"]
    check("garage follows dim", ga.follows_dim, False)
    sw = SW.AllDimSwitch(); sw.hass = hass; sw.entity_id = "switch.roomcontrol_generiek_alles_dim"
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 18, 21, 0)):
        await sw.async_added_to_hass(); await asyncio.sleep(0.2)
    check("21:00 outside window", (wk.dimmed, hass.states.get(sw.entity_id).state), (False, "off"))
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 18, 23, 0)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("23:00 window starts: woonkamer dim, garage not", (wk.dimmed, ga.dimmed), (True, False))
    check("switch on (garage ignored)", hass.states.get(sw.entity_id).state, "on")
    check("slots attr", hass.states.get(sw.entity_id).attributes["time_slots"], 2)
    await sw.async_turn_off(); await asyncio.sleep(0.1)
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 19, 1, 0)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("01:00 after 'Alles terug' by hand: stays back", wk.dimmed, False)
    await sw.async_turn_on()
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 19, 7, 0)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("07:00 window ends: all back", wk.dimmed, False)
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 18, 13, 30)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("wed 13:30 second slot: dim", wk.dimmed, True)
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 18, 14, 0)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("wed 14:00 second slot ends: back", wk.dimmed, False)
    with patch.object(SW.dt_util, "now", return_value=datetime(2026, 11, 19, 13, 30)):
        sw._window_tick(); await asyncio.sleep(0.2)
    check("thu 13:30 (slot only on wed): not dim", wk.dimmed, False)
    hass.data[DOMAIN]["settings"] = {}
    sw._on_config(); check("slots removed: timers gone", sw._window_unsubs, [])
    # Follows the alarm (on by default); first switched off explicitly
    hass.data[DOMAIN]["settings"] = {"alarm_entity": "alarm_control_panel.huis", "all_dim_follows_alarm": False}; sw._on_config()
    hass.states.async_set("alarm_control_panel.huis", "armed_home")
    await sw.async_turn_on(); await asyncio.sleep(0.1)
    hass.states.async_set("alarm_control_panel.huis", "disarmed"); await asyncio.sleep(0.2)
    check("option off: disarm changes nothing", wk.dimmed, True)
    hass.data[DOMAIN]["settings"] = {"alarm_entity": "alarm_control_panel.huis"}  # default: follows the alarm
    sw._on_config(); await asyncio.sleep(0.2)
    check("option on while disarmed: all back", wk.dimmed, False)
    hass.states.async_set("alarm_control_panel.huis", "armed_home"); await asyncio.sleep(0.2)
    check("armed home: all dim", (wk.dimmed, hass.states.get(sw.entity_id).state), (True, "on"))
    hass.states.async_set("alarm_control_panel.huis", "armed_night"); await asyncio.sleep(0.1)
    check("armed night: stays dim", wk.dimmed, True)
    hass.states.async_set("alarm_control_panel.huis", "disarmed"); await asyncio.sleep(0.3)
    check("disarmed: all back", (wk.dimmed, hass.states.get(sw.entity_id).state), (False, "off"))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
