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
    hass.data[DOMAIN] = {"settings": {"persons": [], "alarm": {}}}
    for p in ("person.paul", "person.sarah"): hass.states.async_set(p, "not_home")
    hass.states.async_set("sensor.home_paul_distance", "250", {"unit_of_measurement": "km"})
    a = A.AlarmAutomation(hass)
    check("nobody chosen anywhere: all HA persons", a.persons(), ["person.paul", "person.sarah"])
    check("Paul's Proximity sensor found", a.distance_sensors(), {"person.paul": "sensor.home_paul_distance"})
    check("Sarah unknown → within limit → near: Armed Away (since 2.2.0)", a.away_target(), "armed_away")
    hass.states.async_set("sensor.home_sarah_distance", "180", {"unit_of_measurement": "km"})
    check("both via Proximity, closest 180 → vacation", (a.distance_km(), a.away_target()), (180.0, "armed_vacation"))
    hass.data[DOMAIN]["settings"]["persons"] = ["person.paul"]
    check("Presence persons win over all HA persons", a.persons(), ["person.paul"])
    hass.data[DOMAIN]["settings"]["alarm"] = {"persons": ["person.sarah"], "distance_sensors": {"person.paul": "sensor.home_sarah_distance"}}
    check("an alarm-own person list is ignored; chosen sensor wins over auto", (a.persons(), a.distance_sensors()), (["person.paul"], {"person.paul": "sensor.home_sarah_distance"}))
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
