import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
from roomcontrol.switch import AllDimSwitch

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    calls = []
    async def rec(c): calls.append((c.service, c.data.get("entity_id"), c.data.get("brightness")))
    for s in ("turn_on", "turn_off"): hass.services.async_register("light", s, rec)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    rooms = []
    for name, lamp in (("Woonkamer", "light.wk"), ("Keuken", "light.kk"), ("Zolder", "light.zo")):
        a = ar.async_get(hass).async_create(name)
        hass.states.async_set(lamp, "on", {"brightness": 200})
        rooms.append({"area_id": a.id, "lights": [{"entity_id": lamp}], **({"hidden": True} if name == "Zolder" else {})})
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {}, "entities": {}}
    for r, lamp in zip(rooms, ("light.wk", "light.kk", "light.zo")):
        e = RoomControlLight(hass, r["area_id"]); e.hass = hass; e.entity_id = f"light.rc_{lamp[6:]}"
        e._members = [lamp]; await e.async_added_to_hass(); e.async_write_ha_state()
    sw = AllDimSwitch(); sw.hass = hass; sw.entity_id = "switch.roomcontrol_generiek_alles_dim"
    await sw.async_added_to_hass()
    print("before:", hass.states.get(sw.entity_id).state)
    await sw.async_turn_on(); await asyncio.sleep(0.3)
    st = hass.states.get(sw.entity_id)
    print("after on:", st.state, st.attributes.get("dimmed_rooms"))
    ents = hass.data[DOMAIN]["entities"]
    print("dimmed per room:", {r["area_id"]: ents[r["area_id"]].dimmed for r in rooms}, "(zolder hidden: not touched)")
    # One room un-dimmed by hand → switch off
    await ents[rooms[0]["area_id"]].async_set_dim(False); await asyncio.sleep(0.3)
    print("one room restored:", hass.states.get(sw.entity_id).state)
    await sw.async_turn_off(); await asyncio.sleep(0.3)
    print("after off:", hass.states.get(sw.entity_id).state, {r["area_id"]: ents[r["area_id"]].dimmed for r in rooms})
    await hass.async_stop()
asyncio.run(main())
