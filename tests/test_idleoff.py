import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10}); hass.states.async_set("binary_sensor.pir", "off")
    hass.states.async_set("light.lees", "on", {"brightness": 200}); hass.states.async_set("light.plafond", "on", {"brightness": 200})
    a = ar.async_get(hass).async_create("Woonkamer")
    room = {"area_id": a.id, "lights": [{"entity_id": "light.lees"}, {"entity_id": "light.plafond"}], "motion_sensors": ["binary_sensor.pir"],
            "groups": [{"id": "g1", "name": "Leeslamp", "lights": ["light.lees"], "idle_off": True}, {"id": "g2", "name": "Plafond", "lights": ["light.plafond"]}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc"; e._members = ["light.lees", "light.plafond"]
    await e.async_added_to_hass(); e._on_by_motion = False
    print("idle lamps (switched on by hand):", e._idle_lamps(), "| grace running:", e._cancel_motion_off is not None or e._grace_until is not None)
    await hass.async_stop()
asyncio.run(main())
