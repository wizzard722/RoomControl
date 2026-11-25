import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.util import dt as dt_util
import roomcontrol.energy as E
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phases":1,"phase_sensors":{"L1":"sensor.net"},"charger_room":"garage","soc_sensor":"sensor.soc","battery_kwh":10,"charge_from_kw":1.2}}}
    en=E.Energy(hass); t=[dt_util.utcnow()]; E.dt_util.utcnow=lambda: t[0]
    S("sensor.soc","50",{"unit_of_measurement":"%"})
    for i in range(4):
        S("sensor.net","3700",{"unit_of_measurement":"W"}); en._tick(); t[0]+=timedelta(minutes=30)
    c=en.status()["car"]; print("after 1.5 h at 3.7 kW, Audi still 50%:", c["soc"], "→ est", c["soc_est"], "| since reading", c["kwh_since_soc"], "kWh")
    S("sensor.soc","90",{"unit_of_measurement":"%"}); en._tick(); c=en.status()["car"]
    print("Audi updates to 90%:", c["soc"], "→ est", c["soc_est"], en.kwh_since_soc, en._soc_seen)
    await hass.async_stop()
asyncio.run(main())
