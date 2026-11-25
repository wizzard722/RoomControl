import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.light import RoomControlLight
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set
    S("light.a","off"); S("light.b","off"); S("light.c","off")
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass; e.entity_id="light.rc"
    RoomControlLight._members=property(lambda self: ["light.a","light.b","light.c"])
    ROOM={"groups":[{"id":"g1","lights":["light.a"],"late_home":True},{"id":"g2","lights":["light.b"]},{"id":"g3","lights":["light.c"],"late_home":False}]}
    RoomControlLight._room=property(lambda self: ROOM)
    e._evening_lamps=lambda: []; e._lux_lamps_now=lambda: []; e._own_active=lambda: []
    e._late_pending=False; e._late_on_done=False; RoomControlLight._manual=property(lambda self: False); e._sun_down=lambda: True
    calls=[]
    async def call(svc, lamps=None, levels=None): calls.append((svc, lamps))
    e._async_call=call; e._dbg=lambda *a, **k: None; e._on_by_motion=False
    hass.data["roomcontrol"]={"late_home_active":{"person.p"}}
    print("late lamps (room off):", e._late_lamps())
    ROOM["late_home"]=True
    print("late lamps (room on, g2 follows):", e._late_lamps())
    ROOM["late_home"]=False
    e._on_late_home(); await hass.async_block_till_done()
    print("turned on:", calls); calls.clear()
    S("light.a","on"); S("light.b","on")
    e._auto_off("no motion", lamps=["light.a","light.b"]); await hass.async_block_till_done()
    print("auto off with late home:", calls, "pending", e._late_pending); calls.clear()
    print("off lamps when home:", e.late_home_off_lamps())
    ROOM["groups"][0]["late_home"]=False
    print("holds with none:", e._late_home_holds())
    await hass.async_stop()
asyncio.run(main())
