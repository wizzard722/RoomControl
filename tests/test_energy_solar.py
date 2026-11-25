import asyncio, sys, tempfile, types
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
import roomcontrol.energy as E
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    S = hass.states.async_set
    for p, c, r in (("l1", 300, 0), ("l2", 0, 900), ("l3", 100, 0)):
        S(f"sensor.c_{p}", str(c), {"unit_of_measurement": "W"}); S(f"sensor.r_{p}", str(r), {"unit_of_measurement": "W"})
    S("sensor.solar", "3.0", {"unit_of_measurement": "kW"}); S("sensor.batt", "-600", {"unit_of_measurement": "W"})
    base = {"phases": 3, "phase_sensors": {"L1": "sensor.c_l1", "L2": "sensor.c_l2", "L3": "sensor.c_l3"},
            "produced_sensors": {"L1": "sensor.r_l1", "L2": "sensor.r_l2", "L3": "sensor.r_l3"},
            "charger_room": "garage", "charger_phase": "L1", "charge_from_kw": 1.2}
    hass.data[DOMAIN] = {"rooms": [{"area_id": "garage", "phase": "L1"}], "settings": {"energy": dict(base)}}
    with patch.object(E, "managed_areas", lambda h: {"garage"}):
        e = E.Energy(hass)
        check("no solar flag: produced ignored", e.status()["phases"], {"L1": 300.0, "L2": 0.0, "L3": 100.0})
        hass.data[DOMAIN]["settings"]["energy"] = {**base, "has_solar": True}
        check("solar flag, no solar sensor: consumed − returned", e.status()["phases"], {"L1": 300.0, "L2": -900.0, "L3": 100.0})
        hass.data[DOMAIN]["settings"]["energy"] = {**base, "has_solar": True, "solar_sensor": "sensor.solar", "solar_phase": "all"}
        st = e.status()
        check("solar 3 kW over 3 phases", st["phases"], {"L1": 1300.0, "L2": 100.0, "L3": 1100.0})
        import datetime as _dt
        e._above_since -= _dt.timedelta(seconds=91); st = e.status()  # over the limit for CHARGE_CONFIRM (90 s)
        check("car estimate on L1 = 1.3 kW → charging", (st["car"]["estimate_kw"], st["car"]["charging"]), (1.3, True))
        check("detail for the charger's phase", st["car"]["phase_detail"], {"consumed": 300.0, "produced": 0.0, "solar": 1000.0, "battery": None})
        hass.data[DOMAIN]["settings"]["energy"] = {**base, "has_solar": True, "solar_sensor": "sensor.solar", "solar_phase": "L2",
                                                  "has_battery": True, "battery_sensor": "sensor.batt", "battery_phase": "L1"}
        st = e.status()
        check("solar on L2; a home battery is ignored since 3.0.7", st["phases"], {"L1": 300.0, "L2": 2100.0, "L3": 100.0})
        S("sensor.pv1", "800", {"unit_of_measurement": "W"}); S("sensor.pv2", "1.2", {"unit_of_measurement": "kW"})
        hass.data[DOMAIN]["settings"]["energy"] = {**base, "has_solar": True, "solar_sensors": {"L1": "sensor.pv1", "L2": "sensor.pv2"}, "solar_sensor": "sensor.solar"}
        st = e.status()
        check("solar per phase wins over the single sensor", st["phases"], {"L1": 1100.0, "L2": 300.0, "L3": 100.0})
        check("detail shows the phase's solar", st["car"]["phase_detail"]["solar"], 800.0)
        hass.data[DOMAIN]["settings"]["energy"] = {"phases": 1, "phase_sensors": {"L1": "sensor.c_l1"}, "produced_sensors": {"L1": "sensor.r_l2"},
                                                  "has_solar": True, "solar_sensor": "sensor.solar", "solar_phase": "L3"}
        check("1 phase: everything on L1", e.status()["phases"], {"L1": 300 - 900 + 3000.0})
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
