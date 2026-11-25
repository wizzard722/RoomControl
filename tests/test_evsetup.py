import asyncio, sys, tempfile, types, traceback
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from roomcontrol.const import DOMAIN
import roomcontrol.sensor as S
from roomcontrol.entity_ids import _suggest
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    hass.data[DOMAIN] = {"rooms": [], "settings": {}}
    for cls in (S.EvChargingSensor,):
        e = cls()
        try:
            _suggest(hass, "sensor", e); print(cls.__name__, "entity_id:", e.entity_id)
        except Exception:
            traceback.print_exc()
    c = S.CoversStateSensor("woonkamer")
    try:
        _suggest(hass, "sensor", c); print("covers entity_id:", c.entity_id)
    except Exception: traceback.print_exc()
    await hass.async_stop()
asyncio.run(main())
