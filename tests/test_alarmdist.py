import sys, tempfile, types, asyncio
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    cfg = {"distance_sensors": {"person.paul": "sensor.paul", "person.sarah": "sensor.sarah"}, "distance_km": 100}
    hass.data[DOMAIN] = {"settings": {"persons": ["person.paul", "person.sarah"], "alarm": cfg}}
    a = A.AlarmAutomation(hass)
    hass.states.async_set("sensor.paul", "150000", {"unit_of_measurement": "m"}); hass.states.async_set("sensor.sarah", "unknown")
    check("Paul 150 km, Sarah unknown → within limit", (a.distance_km(), a.away_target()), (0.0, "armed_away"))
    hass.states.async_set("sensor.sarah", "220", {"unit_of_measurement": "km"})
    check("both known and far → closest 150 km → vacation", (a.distance_km(), a.away_target()), (150.0, "armed_vacation"))
    hass.states.async_set("sensor.sarah", "40", {"unit_of_measurement": "km"})
    check("Sarah 40 km → closest decides → home", a.away_target(), "armed_away")
    cfg["distance_sensors"] = {"person.paul": "sensor.paul"}
    check("Sarah without sensor → within limit", a.away_target(), "armed_away")
    cfg["distance_sensors"] = {}; cfg["distance_sensor"] = "sensor.paul"
    check("older single sensor for everyone: 150 km → vacation", a.away_target(), "armed_vacation")
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
