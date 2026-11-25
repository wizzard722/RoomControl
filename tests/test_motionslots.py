import asyncio, sys, tempfile, types
from unittest.mock import patch
from datetime import datetime
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.rooms import motion_slots, motion_window
from roomcontrol.light import RoomControlLight
import roomcontrol.light as L

ok = True
def check(label, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + label)

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    hass.data[DOMAIN] = {"rooms": [
        {"area_id": "hal", "motion_sensors": ["binary_sensor.old", "binary_sensor.new", "binary_sensor.none", "binary_sensor.dark"],
         "motion_windows": {"binary_sensor.old": {"start": "07:00", "end": "23:00"},
                            "binary_sensor.new": [
                                {"days": [0,1,2,3,4], "start": {"type": "time", "time": "07:00"}, "end": {"type": "time", "time": "09:00"}},
                                {"days": [5,6], "start": {"type": "time", "time": "22:00"}, "end": {"type": "time", "time": "02:00"}},
                                {"days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "12:00"}, "end": {"type": "time", "time": "13:00"}, "holiday": "vacation"}],
                            "binary_sensor.none": [],
                            "binary_sensor.dark": [{"days": [0,1,2,3,4,5,6], "start": {"type": "dark"}, "end": {"type": "sunrise"}}]}},
    ], "entities": {}}
    check("old window read as one slot", len(motion_slots(hass, "binary_sensor.old")) == 1 and motion_window(hass, "binary_sensor.old") == (420, 1380))
    check("empty list = always", motion_slots(hass, "binary_sensor.none") is None)
    e = RoomControlLight.__new__(RoomControlLight); e.hass, e._area_id = hass, "hal"
    sun = {"down": False}
    e._sun_down = lambda: sun["down"]; e._phase = lambda: "dark" if sun["down"] else "light"
    def at(dt, sensor):
        with patch.object(L.dt_util, "now", return_value=dt):
            return e._sensor_in_window(sensor)
    # 2026-11-18 is a Wednesday
    check("Wed 08:00 in weekday slot", at(datetime(2026,11,18,8,0), "binary_sensor.new"))
    check("Wed 10:00 outside", not at(datetime(2026,11,18,10,0), "binary_sensor.new"))
    check("Sat 23:00 in weekend slot", at(datetime(2026,11,21,23,0), "binary_sensor.new"))
    check("Sun 01:00 carry from Sat", at(datetime(2026,11,22,1,0), "binary_sensor.new"))
    check("Mon 01:00 carry from Sun", at(datetime(2026,11,23,1,0), "binary_sensor.new"))
    check("Tue 01:00 no carry (Mon not weekend)", not at(datetime(2026,11,24,1,0), "binary_sensor.new"))
    check("Wed 12:30 vacation slot not normally", not at(datetime(2026,11,18,12,30), "binary_sensor.new"))
    hass.data[DOMAIN]["vacation"] = True
    check("vacation: 12:30 vacation slot", at(datetime(2026,11,18,12,30), "binary_sensor.new"))
    check("vacation: 08:00 normal slot not", not at(datetime(2026,11,18,8,0), "binary_sensor.new"))
    hass.data[DOMAIN]["vacation"] = False
    check("old window 12:00", at(datetime(2026,11,18,12,0), "binary_sensor.old"))
    check("old window 02:00 outside", not at(datetime(2026,11,18,2,0), "binary_sensor.old"))
    check("no slots always", at(datetime(2026,11,18,3,0), "binary_sensor.none"))
    check("dark slot during day: no", not at(datetime(2026,11,18,14,0), "binary_sensor.dark"))
    sun["down"] = True
    check("dark slot at 19:00 dark: yes", at(datetime(2026,11,18,19,0), "binary_sensor.dark"))
    check("dark slot 05:00 before sunrise: yes", at(datetime(2026,11,18,5,0), "binary_sensor.dark"))
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
