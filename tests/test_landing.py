import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, floor_registry as fr
from roomcontrol.const import DOMAIN
from roomcontrol.rooms import room_neighbours
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await fr.async_load(hass); await ar.async_load(hass)
    f = fr.async_get(hass); a = ar.async_get(hass)
    bg = f.async_create("Begane grond", level=0); v1 = f.async_create("1e verdieping", level=1); v2 = f.async_create("Zolder", level=2)
    hal = a.async_create("Hal", floor_id=bg.floor_id); ov = a.async_create("Overloop", floor_id=v1.floor_id)
    zo = a.async_create("Zolderoverloop", floor_id=v2.floor_id); wk = a.async_create("Woonkamer", floor_id=bg.floor_id)
    hass.data[DOMAIN] = {"settings": {"layout": {"links": [{"a": hal.id, "b": wk.id, "kind": "door"}], "landings": [hal.id, ov.id, zo.id]}}}
    for area in (hal, ov, zo, wk):
        print(area.name, "→", [(a.async_get_area(n["area_id"]).name, n["kind"]) for n in room_neighbours(hass, area.id)])
asyncio.run(main())
