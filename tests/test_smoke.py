import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    await hass.async_start()
    calls = []
    async def rec(call): calls.append((call.domain, call.service, call.data.get("entity_id")))
    for svc in ("turn_on", "turn_off"): hass.services.async_register("light", svc, rec)
    for svc in ("open_cover", "close_cover"): hass.services.async_register("cover", svc, rec)
    area = ar.async_get(hass).async_create("Woonkamer")
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10, "rising": False})
    hass.states.async_set("light.lamp", "off")
    hass.states.async_set("binary_sensor.wk", "off")
    room = {"area_id": area.id, "lights": [{"entity_id": "light.lamp"}], "motion_sensors": ["binary_sensor.wk"],
            "schedules": ["schedule.oud"],  # leftover config: must be ignored
            "covers": ["cover.wk"], "covers_follow": True, "covers_open_at": "light"}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    e = RoomControlLight(hass, area.id)
    e.hass = hass; e.entity_id = "light.woonkamer"
    try:
        e._members = ["light.lamp"]
        await e.async_added_to_hass()
    except Exception as ex:
        import traceback; traceback.print_exc()
    e.async_write_ha_state()
    st = hass.states.get("light.woonkamer")
    print("state ok:", st is not None, "no schedule attrs:", "active_schedule" not in st.attributes)
    hass.states.async_set("binary_sensor.wk", "on"); await asyncio.sleep(0.2)
    print("motion ->", calls)
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 2, "rising": True}); await asyncio.sleep(0.2)
    print("sunrise ->", calls[-1])
    print("debug_now keys:", sorted(k for k in e.debug_now() if "sched" in k))
    await hass.async_stop()
asyncio.run(main())
