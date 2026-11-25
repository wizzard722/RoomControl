import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.alarm_auto as A
from roomcontrol.light import RoomControlLight
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set
    S("light.hal","on"); S("light.keuken","on"); S("light.wc","off")
    # a room entity with real late_home_off_lamps, members hal + keuken; keuken's bundle slot runs
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass
    RoomControlLight._members=property(lambda self: ["light.hal","light.keuken","light.wc"])
    e._evening_lamps=lambda: []; e._lux_lamps_now=lambda: []; e._own_active=lambda: ["light.keuken"]
    e._late_pending=True; RoomControlLight._room=property(lambda self: {"late_home": True})
    hass.data["roomcontrol"]={"entities":{"hal":e},"settings":{},"rooms":[]}
    print("go off:", e.late_home_off_lamps())
    a=A.AlarmAutomation(hass)
    print("message 'lampen uit':", a.arrive_lights_go_off())
    e._own_active=lambda: ["light.keuken","light.hal"]
    print("all held by time slots → go off:", e.late_home_off_lamps(), "| message:", a.arrive_lights_go_off())
    await hass.async_stop()
asyncio.run(main())
