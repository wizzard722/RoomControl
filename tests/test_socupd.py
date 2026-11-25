import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.util import dt as dt_util
import roomcontrol.energy as E
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phases":1,"phase_sensors":{"L1":"sensor.net"},"charger_room":"garage","soc_sensor":"sensor.soc","battery_kwh":10,"charge_from_kw":1.2,"charger_max_kw":3.7}}}
    en=E.Energy(hass); t=[dt_util.utcnow()]; E.dt_util.utcnow=lambda: t[0]
    S("sensor.net","3700",{"unit_of_measurement":"W"}); S("sensor.soc","40",{"unit_of_measurement":"%"})
    def tick(mins=30):
        en._tick(); t[0]+=timedelta(minutes=mins)
    tick(2)   # over the limit for CHARGE_CONFIRM (90 s) first: then it counts as charging
    tick(); tick(); tick()   # 2 x 30 min integrated: 3.7 kWh → +33.3%
    est=lambda: en.status()["car"]["soc_est"]
    check("estimate after 1 h", est(), 73.3)
    S("sensor.soc","82",{"unit_of_measurement":"%"}); tick()   # 30 more min: estimate ~90; car reports 82 (late)
    e1=est(); check("car reports 82% while estimate ~90: no jump back", (e1 >= 89.9, round(en.kwh_since_soc,2)), (True, 0.88))
    en._soc_value, en.kwh_since_soc = 50.0, 2.0   # estimate 50 + 18 = 68%
    S("sensor.soc","75",{"unit_of_measurement":"%"}); en._take_reading(hass.data["roomcontrol"]["settings"]["energy"], 75.0)
    check("car reports 75% (higher than the 68% estimate): 75 counts, extra 0", (round(en._soc_value), en.kwh_since_soc), (75, 0.0))
    S("sensor.soc","60",{"unit_of_measurement":"%"}); tick(0)
    check("car reports 60% (30 below): the car wins", est(), 60.0)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
