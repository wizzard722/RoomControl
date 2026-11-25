import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
import roomcontrol.binary_sensor as B
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    a = ar.async_get(hass).async_create("Slaapkamer")
    hass.data[DOMAIN] = {"rooms": [{"area_id": a.id, "covers": ["cover.a"]}], "settings": {}}
    added = []
    entry = types.SimpleNamespace(async_on_unload=lambda f: None)
    with __import__("unittest.mock").mock.patch.object(B, "managed_areas", return_value={a.id}):
        await B.async_setup_entry(hass, entry, lambda ents, *a, **k: added.extend(ents))
    print([e.entity_id for e in added])
    await hass.async_stop()
asyncio.run(main())
