import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight

async def scenario(label, daylight, lamp_min=0, gain=None, start=200):
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    lamp = "light.lamp"
    def lux_now():
        st = hass.states.get(lamp); b = st.attributes.get("brightness", 0) if st.state == "on" else 0
        return daylight + b * 2  # lamps: 2 lux per brightness step
    async def on(c):
        b = c.data.get("brightness") or (round(c.data["brightness_pct"] * 2.55) if "brightness_pct" in c.data else 255)
        b = max(b, lamp_min)
        hass.states.async_set(lamp, "on", {"brightness": b}); hass.states.async_set("sensor.lux", str(lux_now()))
    async def off(c):
        hass.states.async_set(lamp, "off"); hass.states.async_set("sensor.lux", str(lux_now()))
    hass.services.async_register("light", "turn_on", on); hass.services.async_register("light", "turn_off", off)
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 30})
    a = ar.async_get(hass).async_create("Kantoor")
    hass.states.async_set(lamp, "on", {"brightness": start})
    hass.states.async_set("sensor.lux", str(lux_now()))
    room = {"area_id": a.id, "lights": [{"entity_id": lamp}], "lux_sensors": ["sensor.lux"], "target_lux": 300,
            "groups": [{"id": "g1", "lights": [lamp], "lux_control": True, "own_times": True,
                        "slots": [{"days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "00:00"}, "end": {"type": "time", "time": "23:59"}}]}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_k"; e._members = [lamp]
    await e.async_added_to_hass()
    if gain: e._lux_gain = gain
    t = dt_util.utcnow(); trail = []
    for i in range(40):
        t += timedelta(seconds=40)
        e._regulate_lux(now=t); await asyncio.sleep(0.02)
        st = hass.states.get(lamp); trail.append(st.attributes.get("brightness") if st.state == "on" else "off")
        if trail[-1] == "off": break
    print(f"{label}: {' '.join(map(str, trail[:14]))}{' …' if len(trail) > 14 else ''} | lux {lux_now()}")
    await hass.async_stop()
    return trail[-1]

async def main():
    r = [
        await scenario("veel daglicht (500 lux)", 500) == "off",
        await scenario("lamp kan niet onder 10", 500, lamp_min=10) == "off",
        await scenario("geleerd model, groot effect", 340, gain=60) == "off",
    ]
    m = await scenario("goed niveau zoeken (daglicht 100)", 100)
    print("ALL PASS" if all(r) and m != "off" else f"RESULT {r} {m}")
asyncio.run(main())
