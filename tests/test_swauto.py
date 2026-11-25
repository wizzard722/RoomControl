import asyncio, os, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.room_switches as RS
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class FakeLight:
    def __init__(self): self.motion = False; self._last_motion_at = None
    def _own_motion(self): return self.motion
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for s in ("turn_on", "turn_off"):
        async def h(c, s=s):
            ids = c.data["entity_id"]; ids = ids if isinstance(ids, list) else [ids]
            for e in ids: calls.append((s, e)); hass.states.async_set(e, "on" if s == "turn_on" else "off")
        hass.services.async_register("switch", s, h)
    light = FakeLight()
    room = {"area_id": "huiskamer", "door_sensors": ["binary_sensor.raam"], "switches": [
        {"entity_id": "switch.soldeer", "off_after": 120},
        {"entity_id": "switch.radio", "off_after": 30, "off_after_from": "motion"},
        {"entity_id": "switch.ir", "kind": "heater", "temp_sensor": "sensor.t", "off_at_temp": 21.0, "off_after": 180, "off_on": ["window"]},
        {"entity_id": "switch.koelkast", "may_off": False, "off_after": 1}]}
    hass.data[DOMAIN] = {"rooms": [room], "entities": {"huiskamer": light}, "settings": {}}
    patch.object(RS, "managed_areas", lambda h: {"huiskamer"}).start()
    for e in ("switch.soldeer", "switch.radio", "switch.ir", "switch.koelkast"): hass.states.async_set(e, "on")
    hass.states.async_set("sensor.t", "19.0"); hass.states.async_set("binary_sensor.raam", "off")
    r = RS.RoomSwitches(hass)
    t0 = dt_util.utcnow(); clock = {"t": t0}
    patch.object(RS.dt_util, "utcnow", lambda: clock["t"]).start()
    async def tick(minutes):
        clock["t"] = clock["t"] + timedelta(minutes=minutes); r._auto_off_tick(); await hass.async_block_till_done()
    light._last_motion_at = t0
    await tick(20); check("20 min: nothing off", calls, [])
    light._last_motion_at = clock["t"]  # motion at 20 min
    await tick(20); check("40 min: radio stays (motion at 20 min)", calls, [])
    await tick(15); check("55 min: radio off (30 min since motion)", calls, [("turn_off", "switch.radio")])
    calls.clear()
    # heater: 19 → 21 °C
    for v in (19.5, 20.0, 20.5):
        hass.states.async_set("sensor.t", str(v)); await tick(5)
    check("heater rising: still on", calls, [])
    check("heater eta", r.heater_eta("switch.ir", 21.0) is not None, True)
    hass.states.async_set("sensor.t", "21.0"); await tick(5)
    check("heater off at 21 °C", calls, [("turn_off", "switch.ir")])
    calls.clear()
    # switched on while already warm: stays on
    hass.states.async_set("switch.ir", "on"); await tick(1)
    check("on while warm: stays on", calls, [])
    hass.states.async_set("sensor.t", "20.0"); await tick(1); hass.states.async_set("sensor.t", "21.2"); await tick(1)
    check("dropped and warm again: off", calls, [("turn_off", "switch.ir")])
    calls.clear()
    # window open
    hass.states.async_set("switch.ir", "on"); hass.states.async_set("sensor.t", "18.0"); hass.states.async_set("binary_sensor.raam", "on"); await tick(1)
    check("window open: heater off", calls, [("turn_off", "switch.ir")])
    calls.clear(); hass.states.async_set("binary_sensor.raam", "off")
    # timer from on: soldeer (on at t0) off after 120 min; koelkast never
    await tick(70)
    check("120 min: soldeer off, koelkast (never off) stays", sorted(calls), [("turn_off", "switch.soldeer")])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
