import asyncio, sys, tempfile, types
from unittest.mock import patch
from datetime import datetime
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.rooms import in_window, motion_window
from roomcontrol.light import RoomControlLight
import roomcontrol.light as L

ok = True
def check(label, cond):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + label)

check("day window inside", in_window((7*60, 23*60), 12*60))
check("day window outside", not in_window((7*60, 23*60), 23*60+30))
check("midnight window late", in_window((7*60, 60), 23*60+30))
check("midnight window early", in_window((7*60, 60), 30))
check("midnight window outside", not in_window((7*60, 60), 3*60))
check("no window = always", in_window(None, 3*60))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    hass.data[DOMAIN] = {"rooms": [
        {"area_id": "hal", "motion_sensors": ["binary_sensor.hal1", "binary_sensor.hal2"],
         "motion_windows": {"binary_sensor.hal1": {"start": "07:00", "end": "23:00"},
                            "binary_sensor.hal2": {"start": "08:00"}}},  # incomplete → always
    ], "entities": {}}
    check("window read", motion_window(hass, "binary_sensor.hal1") == (420, 1380))
    check("incomplete window = always", motion_window(hass, "binary_sensor.hal2") is None)
    e = RoomControlLight.__new__(RoomControlLight); e.hass, e._area_id = hass, "hal"
    hass.states.async_set("binary_sensor.hal1", "on"); hass.states.async_set("binary_sensor.hal2", "off")
    with patch.object(L.dt_util, "now", return_value=datetime(2026, 11, 18, 2, 0)):
        check("02:00 sensor1 outside", not e._sensor_in_window("binary_sensor.hal1"))
        check("02:00 no switching motion", not e._any_motion(switching=True))
        check("02:00 motion still keeps lights on", e._any_motion())
    with patch.object(L.dt_util, "now", return_value=datetime(2026, 11, 18, 12, 0)):
        check("12:00 switching motion", e._any_motion(switching=True))
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
