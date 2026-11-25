import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
import roomcontrol.binary_sensor as B
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    S("binary_sensor.pir_a","off"); S("binary_sensor.pir_b","off")
    hass.data["roomcontrol"]={"rooms":[{"area_id":"woonkamer","motion_sensors":["binary_sensor.pir_a","binary_sensor.pir_b"]}],"settings":{}}
    B.stored_room=lambda h,a: h.data["roomcontrol"]["rooms"][0]
    s=B.RoomMotionSensor("woonkamer"); s.hass=hass; s.entity_id="binary_sensor.roomcontrol_woonkamer_beweging"
    s._refresh(); check("both off → off", s.is_on, False)
    S("binary_sensor.pir_b","on"); await hass.async_block_till_done()
    check("b on → on, b listed", (s.is_on, s.extra_state_attributes["motion_now"]), (True, ["binary_sensor.pir_b"]))
    S("binary_sensor.pir_a","on"); S("binary_sensor.pir_b","off"); await hass.async_block_till_done()
    check("a on, b off → still on", (s.is_on, s.extra_state_attributes["motion_now"]), (True, ["binary_sensor.pir_a"]))
    S("binary_sensor.pir_a","off"); await hass.async_block_till_done()
    check("all off → off, last motion kept", (s.is_on, s.extra_state_attributes["last_motion"] is not None), (False, True))
    S("binary_sensor.pir_a","unavailable"); await hass.async_block_till_done()
    check("one unavailable: still works from the other", (s.available, s.is_on), (True, False))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
