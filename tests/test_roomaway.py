import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.light import RoomControlLight, LampGroupLight
import roomcontrol.room_switches as RS
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set
    S("person.paul","not_home"); S("person.anne","home"); S("light.a","off"); S("switch.tv","on"); S("switch.koffie","on")
    room={"area_id":"slk","persons":["person.paul"],"groups":[{"id":"g1","lights":["light.a"]}],
          "switches":[{"entity_id":"switch.tv","off_on":["room_away"]},{"entity_id":"switch.koffie","off_on":["nobody_home"]}]}
    hass.data["roomcontrol"]={"settings":{"persons":["person.paul","person.anne"]},"rooms":[room]}
    RS.managed_areas=lambda h: {"slk"}
    # lamps_allowed
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass
    RoomControlLight._room=property(lambda self: room); RoomControlLight._manual=property(lambda self: False); RoomControlLight._members=property(lambda self: ["light.a"]); RoomControlLight._own_active=lambda self: []
    print("auto allowed (paul away):", e.lamps_allowed(["light.a"]), "| by hand:", e.lamps_allowed(["light.a"], by_hand=True))
    calls=[]
    async def cl(svc, lamps, **d): calls.append((svc,lamps))
    e.async_call_lamps=cl
    hass.data["roomcontrol"]["entities"]={"slk":e}
    g=LampGroupLight(hass,"slk","g1"); g._lamps=["light.a"]; g.hass=hass
    await g.async_turn_on(); print("bundle on by hand:", calls)
    # switches
    sw=RS.RoomSwitches(hass); sw._store.async_delay_save=lambda *a,**k: None; sw.start()
    svc=[]
    async def h(call): svc.append((call.service, call.data["entity_id"])); [S(x, "on" if call.service=="turn_on" else "off") for x in call.data["entity_id"]]
    hass.services.async_register("switch","turn_on",h); hass.services.async_register("switch","turn_off",h)
    S("person.paul","home"); await hass.async_block_till_done()
    S("person.paul","not_home"); await hass.async_block_till_done()
    print("paul left (anne home):", svc, sw.room_off); svc.clear()
    S("person.paul","home"); await hass.async_block_till_done()
    print("paul back:", svc, sw.room_off)
    await hass.async_stop()
asyncio.run(main())
