from datetime import timedelta
import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
import roomcontrol.energy as E
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phases":1,"phase_sensors":{"L1":"sensor.net"},"charger_room":"garage","charging_sensor":"binary_sensor.audi_charging","charge_from_kw":1.2}}}
    en=E.Energy(hass)
    S("sensor.net","3500",{"unit_of_measurement":"W"}); S("binary_sensor.audi_charging","off")
    en._above_since=E.dt_util.utcnow()-timedelta(minutes=2); c=en.status()["car"]; check("power 3.5 kW, Audi still 'off' → charging (power)", (c["charging"], c["why"]), (True,"power"))
    S("sensor.net","300",{"unit_of_measurement":"W"}); S("binary_sensor.audi_charging","on")
    c=en.status()["car"]; check("low power, Audi 'on' → charging (car)", (c["charging"], c["why"]), (True,"car"))
    S("binary_sensor.audi_charging","off")
    c=en.status()["car"]; check("low power, Audi off → not charging", (c["charging"], c["why"]), (False,"below_limit"))
    d=c["debug"]; check("debug has sensors", (d["consumed"]["entity"], d["consumed"]["state"], d["car_charging_sensor"]["state"], d["estimate_kw"]), ("sensor.net","300","off",0.3))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
