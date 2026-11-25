import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def run(dim):
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    async def on(c):
        ids = c.data["entity_id"] if isinstance(c.data["entity_id"], list) else [c.data["entity_id"]]
        for e in ids:
            b = c.data.get("brightness") or (round(c.data["brightness_pct"] * 255 / 100) if "brightness_pct" in c.data else 255)
            hass.states.async_set(e, "on", {"brightness": b})
    async def off(c):
        ids = c.data["entity_id"] if isinstance(c.data["entity_id"], list) else [c.data["entity_id"]]
        for e in ids: hass.states.async_set(e, "off", {})
    hass.services.async_register("light", "turn_on", on); hass.services.async_register("light", "turn_off", off)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    P = "alarm_control_panel.huis"; hass.states.async_set(P, "disarmed")
    hass.states.async_set("binary_sensor.pir", "off")
    hass.states.async_set("light.a", "on", {"brightness": 200}); hass.states.async_set("light.b", "off", {}); hass.states.async_set("light.c", "on", {"brightness": 180})
    a = ar.async_get(hass).async_create("Slaapkamer")
    room = {"area_id": a.id, "lights": [{"entity_id": "light.a"}, {"entity_id": "light.b"}, {"entity_id": "light.c"}], "motion_sensors": ["binary_sensor.pir"],
            "alarm_entity": P, "armed_home_mode": "no_motion", "armed_home_dim": dim,
            "groups": [{"id": "g1", "name": "Plafond", "lights": ["light.a"]}, {"id": "g2", "name": "Lees", "lights": ["light.b"]}, {"id": "g3", "name": "Kast", "lights": ["light.c"], "dim": False}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_sk"; e._members = ["light.a", "light.b", "light.c"]
    await e.async_added_to_hass(); hass.bus.async_fire("homeassistant_started"); await asyncio.sleep(0.3)
    hass.states.async_set(P, "armed_home"); await asyncio.sleep(0.5)
    st = lambda x: (hass.states.get(x).state, hass.states.get(x).attributes.get("brightness"))
    return hass, e, st

async def main():
    hass, e, st = await run(True)
    check("dim: room in Dim mode", e.dimmed, True)
    check("dim: Plafond stays on, dimmed", st("light.a")[0] == "on" and st("light.a")[1] < 20, True)
    check("dim: Lees stays off", st("light.b")[0], "off")
    check("dim: Kast (no Dim) keeps its level", st("light.c"), ("on", 180))
    hass.states.async_set("binary_sensor.pir", "on"); await asyncio.sleep(0.3)
    check("dim: motion switches nothing on", st("light.b")[0], "off")
    hass.states.async_set("binary_sensor.pir", "off")
    hass.states.async_set("light.b", "on", {"brightness": 255}); await asyncio.sleep(0.6)
    check("dim: switched on by hand → Dim", st("light.b")[0] == "on" and st("light.b")[1] < 20, True)
    check("dim: wants", next(b for b in e.debug_now()["bundles"] if b["key"] == "group:g1")["wants"], "armed_home_dim")
    hass.states.async_set("alarm_control_panel.huis", "disarmed"); await asyncio.sleep(0.6)
    check("disarmed: Dim off, Plafond back", (e.dimmed, st("light.a")), (False, ("on", 200)))
    await hass.async_stop()
    hass, e, st = await run(False)
    check("no dim: all off", (st("light.a")[0], st("light.c")[0], e.dimmed), ("off", "off", False))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
