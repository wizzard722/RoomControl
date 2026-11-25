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
    S("sensor.l1", "2.6", {"unit_of_measurement": "kW"}); S("sensor.l2", "1100", {"unit_of_measurement": "W"}); S("sensor.l3", "300", {"unit_of_measurement": "W"})
    S("light.plafond", "on", {"brightness": 204}); S("light.spots", "off")
    S("switch.espresso", "on"); S("sensor.espresso_power", "920", {"unit_of_measurement": "W"}); S("switch.koelkast", "on")
    S("light.wk", "on", {"brightness": 255}); S("switch.tv", "on")
    S("sensor.audi_soc", "64"); 
    rooms = [
      {"area_id": "keuken", "phase": "L2", "groups": [{"id": "g1", "name": "Plafond", "lights": ["light.plafond"]}, {"id": "g2", "name": "Spots", "lights": ["light.spots"]}],
       "switches": [{"entity_id": "switch.espresso"}, {"entity_id": "switch.koelkast", "may_off": False}],
       "power": {"bundle:g1": {"watts": 36}, "bundle:g2": {"watts": 25}, "switch:switch.espresso": {"sensor": "sensor.espresso_power"}, "switch:switch.koelkast": {"watts": 85}}},
      {"area_id": "woonkamer", "phase": "L1", "groups": [{"id": "w", "name": "Plafond", "lights": ["light.wk"]}], "switches": [{"entity_id": "switch.tv"}],
       "power": {"bundle:w": {"watts": 30}, "switch:switch.tv": {"watts": 95}}},
      {"area_id": "garage", "phase": "L1"}]
    energy = {"phases": 3, "phase_sensors": {"L1": "sensor.l1", "L2": "sensor.l2", "L3": "sensor.l3"}, "charger_room": "garage", "charger_phase": "L1",
              "charge_from_kw": 1.2, "battery_kwh": 8.8, "car_name": "Audi A3", "soc_sensor": "sensor.audi_soc"}
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {"energy": energy}}
    with patch.object(E, "managed_areas", lambda h: {"keuken", "woonkamer", "garage"}):
        e = E.Energy(hass); st = e.status()
        import datetime as _dt
        e._above_since -= _dt.timedelta(seconds=91); st = e.status()  # over the limit for CHARGE_CONFIRM
        check("keuken watts (36*0.8 + 0 + 920 + 85)", st["rooms"]["keuken"]["watts"], 1033.8)
        check("woonkamer watts", st["rooms"]["woonkamer"]["watts"], 125.0)
        check("phases in W", st["phases"], {"L1": 2600.0, "L2": 1100.0, "L3": 300.0})
        car = st["car"]
        check("car estimate = 2600 - 125 W", (car["estimate_kw"], car["charging"], car["kw"]), (2.48, True, 2.48))
        check("soc and kWh", (car["soc"], car["kwh"], car["name"]), (64.0, 5.6, "Audi A3"))
        check("full_at set", bool(car["full_at"]), True)
        e._tick(); e._last = e._last.replace(year=e._last.year) ; 
        import datetime; e._last -= datetime.timedelta(minutes=30); e._tick()
        check("charged ~1.24 kWh in 30 min", round(e.status()["car"]["charged_kwh"],1), 1.2)
        S("sensor.l1", "0.4", {"unit_of_measurement": "kW"})
        check("not charging below threshold", e.status()["car"]["charging"], False)
        hass.data[DOMAIN]["settings"]["energy"]["charging_sensor"] = "sensor.audi_charging"; S("sensor.audi_charging", "charging")
        c = e.status()["car"]
        check("charging from Audi sensor, kW falls back to max", (c["charging"], c["from_sensor"], c["kw"]), (True, True, 3.7))
        hass.data[DOMAIN]["settings"]["energy"] = {"phases": 1, "phase_sensors": {"L1": "sensor.l1"}, "charger_room": "garage"}
        S("sensor.l1", "3.0", {"unit_of_measurement": "kW"})
        c = e.status()
        check("1 phase: every room on L1", (c["rooms"]["keuken"]["phase"], round(c["car"]["estimate_kw"],2)), ("L1", round((3000-1033.8-125)/1000,2)))
        S("sensor.p_a", "12", {"unit_of_measurement": "W"}); S("sensor.p_b", "0.02", {"unit_of_measurement": "kW"})
        r = {"area_id": "x", "groups": [{"id": "b", "name": "Spots", "lights": ["light.a", "light.b", "light.c"]}],
             "power": {"bundle:b": {"mode": "sensor", "sensors": {"light.a": "sensor.p_a", "light.b": "sensor.p_b", "light.zz": "sensor.p_a"}}}}
        check("per-lamp sensors summed (12 W + 20 W, other lamp ignored)", E.room_parts(hass, r)[0]["watts"], 32.0)
        r["power"]["bundle:b"] = {"sensor": "sensor.p_a"}
        check("old single sensor still works", E.room_parts(hass, r)[0]["watts"], 12.0)
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
