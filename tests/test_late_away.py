import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.light import RoomControlLight
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    S=hass.states.async_set
    S("person.p","not_home"); S("light.a","on"); S("light.b","on")
    ROOM={"persons":["person.p"],"groups":[{"id":"g1","lights":["light.a"],"late_home":True},{"id":"g2","lights":["light.b"]}]}
    hass.data["roomcontrol"]={"settings":{"persons":["person.p"]}}
    RoomControlLight._room=property(lambda self: ROOM); RoomControlLight._manual=property(lambda self: False)
    RoomControlLight._members=property(lambda self: ["light.a","light.b"])
    e=RoomControlLight.__new__(RoomControlLight); e.hass=hass; e.entity_id="light.rc"
    ACT=["light.a","light.b"]
    e._own_active=lambda: list(ACT); e._evening_lamps=lambda: [x for x in ACT]; e._lux_lamps_now=lambda: []
    e._late_pending=False; e._dbg=lambda *a,**k: None; e._on_by_motion=False; e._any_motion=lambda *a,**k: False
    e._alarm_mode=lambda: "normal"
    calls=[]
    async def call(svc, lamps=None, levels=None, **k): calls.append((svc, lamps))
    e._async_call=call
    print("allowed auto (nobody home, slot runs):", e.lamps_allowed(["light.a","light.b"]))
    e._conditions=("dark", True); e._phase=lambda: "dark"; e._allowed=True
    e._evaluate_conditions(); await hass.async_block_till_done()
    print("nobody home → off:", calls); calls.clear()
    # slot ends, Later thuis off
    e._own_prev={"light.a","light.b"}; ACT.clear(); S("light.b","off")
    e._evaluate_own_times(); await hass.async_block_till_done()
    print("slot ends, switch off:", calls, e._late_pending); calls.clear()
    # slot ends with Later thuis on
    ACT[:]=["light.a"]; e._own_prev={"light.a"}; ACT.clear()
    hass.data["roomcontrol"]["late_home_active"]={"person.p"}
    e._evaluate_own_times(); await hass.async_block_till_done()
    print("slot ends, switch on:", calls, "pending", e._late_pending)
    await hass.async_stop()
asyncio.run(main())
