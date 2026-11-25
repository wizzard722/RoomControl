import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from roomcontrol.const import DOMAIN, SIGNAL_CONFIG_UPDATED
from roomcontrol.light import RoomControlLight

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    async def on(c):
        ids = c.data["entity_id"] if isinstance(c.data["entity_id"], list) else [c.data["entity_id"]]
        for e in ids:
            b = c.data.get("brightness") or (round(c.data["brightness_pct"] * 255 / 100) if "brightness_pct" in c.data else 255)
            hass.states.async_set(e, "on", {"brightness": b})
    async def off(c): pass
    hass.services.async_register("light", "turn_on", on); hass.services.async_register("light", "turn_off", off)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    a = ar.async_get(hass).async_create("Woonkamer")
    hass.states.async_set("light.bank", "on", {"brightness": 200}); hass.states.async_set("light.kast", "on", {"brightness": 180})
    room = {"area_id": a.id, "lights": [{"entity_id": "light.bank"}, {"entity_id": "light.kast"}],
            "groups": [{"id": "g1", "lights": ["light.bank"], "dim": True}, {"id": "g2", "lights": ["light.kast"], "dim": False}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {"dim_level": 10}, "entities": {}}
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_wk"; e._members = ["light.bank", "light.kast"]
    await e.async_added_to_hass()
    await e.async_set_dim(True); await asyncio.sleep(0.2)
    b = lambda x: hass.states.get(x).attributes["brightness"]
    check("Dim on: bank at 10%, kast untouched", (b("light.bank"), b("light.kast")), (26, 180))
    room["groups"][1]["dim"] = True; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await asyncio.sleep(0.3)
    check("'Doet mee met Dim' on: kast to 10%", b("light.kast"), 26)
    room["groups"][1]["dim"] = False; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await asyncio.sleep(0.3)
    check("'Doet mee met Dim' off: kast back to 180", b("light.kast"), 180)
    await e.async_set_dim(False); await asyncio.sleep(0.2)
    room["groups"][1]["dim"] = True; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await asyncio.sleep(0.3)
    check("room not on Dim: switching the option changes nothing", b("light.kast"), 180)
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
