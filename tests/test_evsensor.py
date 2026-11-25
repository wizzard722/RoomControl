import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.util import dt as dt_util
import roomcontrol.energy as E
from roomcontrol.sensor import EvChargingSensor
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.language="nl"; await ar.async_load(hass); await hass.async_start()
    garage = ar.async_get(hass).async_create("Garage")
    S=hass.states.async_set
    base=dt_util.utcnow().replace(minute=0,second=0,microsecond=0)
    fc=[{"start_date":(base+timedelta(minutes=15*i)).isoformat(),"end_date":(base+timedelta(minutes=15*(i+1))).isoformat(),"price_tax_included":{"amount":3000000+(i%8)*100000}} for i in range(96)]
    S("sensor.zp","0.3",{"forecast":fc})
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phases":1,"phase_sensors":{"L1":"sensor.net"},"has_solar":True,"solar_sensors":{"L1":"sensor.prod"},"charger_room":garage.id,"car_name":"Audi A3 e-tron","soc_sensor":"sensor.soc","battery_kwh":8.8,"price_sensor":"sensor.zp","charger_max_kw":3.7}}}
    en=E.Energy(hass); hass.data["roomcontrol"]["energy"]=en
    t=[dt_util.utcnow()]; E.dt_util.utcnow=lambda: t[0]
    def step(net, prod, soc):
        S("sensor.net",str(net),{"unit_of_measurement":"W"}); S("sensor.prod",str(prod),{"unit_of_measurement":"W"}); S("sensor.soc",str(soc),{"unit_of_measurement":"%"})
        en._tick(); t[0]+=timedelta(minutes=30)
    step(100,0,40); step(2000,2500,40); step(2000,2500,50); step(4000,0,60); step(100,0,70)   # one session done
    step(2000,2500,70); step(2000,2500,75)  # running
    sens=EvChargingSensor(); sens.hass=hass; sens._refresh()
    a=sens.extra_state_attributes
    for k,v in a.items(): print(f"  {k}: {v}")
    missing=[k for k,v in a.items() if v is None]
    print("state:", sens.native_value, "| empty:", missing)
    await hass.async_stop()
asyncio.run(main())
