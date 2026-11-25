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
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phases":1,"phase_sensors":{"L1":"sensor.net"},"charger_room":"garage","charge_from_kw":1.2}}}
    en=E.Energy(hass); t0=dt_util.utcnow(); clock=[t0]
    E.dt_util.utcnow=lambda: clock[0]
    S("sensor.net","2500",{"unit_of_measurement":"W"})
    c=en.status()["car"]; check("peak just started → confirming", (c["charging"], c["why"]), (False,"confirming"))
    clock[0]=t0+timedelta(seconds=60); c=en.status()["car"]; check("60 s → still confirming", (c["charging"], c["why"]), (False,"confirming"))
    S("sensor.net","300",{"unit_of_measurement":"W"}); clock[0]=t0+timedelta(seconds=70); c=en.status()["car"]; check("oven element off → reset", c["why"], "below_limit")
    S("sensor.net","3500",{"unit_of_measurement":"W"}); clock[0]=t0+timedelta(seconds=80); en.status()
    clock[0]=t0+timedelta(seconds=175); c=en.status()["car"]; check("95 s above → charging", (c["charging"], c["why"]), (True,"power"))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
