import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
from roomcontrol.clocks import SIGNAL_CLOCKS_UPDATED, ClockManager

class FakeClocks:
    ringing = set()
    def lamps_ringing(self, area): return set(self.ringing)

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    calls = []
    async def on(c):
        calls.append(("on", tuple(c.data["entity_id"]) if isinstance(c.data["entity_id"], list) else (c.data["entity_id"],), c.data.get("brightness"), c.data.get("brightness_pct")))
        for e in (c.data["entity_id"] if isinstance(c.data["entity_id"], list) else [c.data["entity_id"]]):
            b = c.data.get("brightness") or (round(c.data["brightness_pct"] * 2.55) if "brightness_pct" in c.data else 255)
            hass.states.async_set(e, "on", {"brightness": b})
    async def off(c): pass
    hass.services.async_register("light", "turn_on", on); hass.services.async_register("light", "turn_off", off)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    a = ar.async_get(hass).async_create("Slaapkamer")
    hass.states.async_set("light.bed", "off"); hass.states.async_set("light.plafond", "off")
    clocks = ClockManager(hass); clocks.ringing = set(); clocks.lamps_ringing = lambda area: set(clocks.ringing)
    hass.data[DOMAIN] = {"rooms": [{"area_id": a.id, "lights": [{"entity_id": "light.bed"}, {"entity_id": "light.plafond"}]}],
                         "settings": {}, "entities": {}, "clocks": clocks}
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_slk"; e._members = ["light.bed", "light.plafond"]
    await e.async_added_to_hass()
    await e.async_set_dim(True); await asyncio.sleep(0.1)
    check("Dim on", e.dimmed, True)
    # Alarm clock goes off for light.bed at 30%
    clocks.ringing = {"light.bed"}; async_dispatcher_send(hass, SIGNAL_CLOCKS_UPDATED)
    calls.clear()
    await e.async_call_lamps("turn_on", ["light.bed"], brightness=round(30 * 255 / 100)); await asyncio.sleep(0.3)
    check("bed during clock not on Dim", "light.bed" in e._dimmed_lamps(), False)
    check("bed burns at clock level (30 % = 76)", hass.states.get("light.bed").attributes["brightness"], round(30 * 255 / 100))
    check("no 1% forced on bed", [c for c in calls if c[3] is not None and "light.bed" in c[1]], [])
    check("plafond still follows Dim", "light.plafond" in e._dimmed_lamps(), True)
    # Last step / stop: clock over
    calls.clear(); clocks.ringing = set(); async_dispatcher_send(hass, SIGNAL_CLOCKS_UPDATED); await asyncio.sleep(0.3)
    check("after clock: bed to Dim level", [c for c in calls if "light.bed" in c[1]], [("on", ("light.bed",), None, 1)])
    await e.async_set_dim(False); await asyncio.sleep(0.2)
    check("Dim off: bed back to clock brightness", hass.states.get("light.bed").attributes["brightness"], round(30 * 255 / 100))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
