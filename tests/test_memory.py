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
from roomcontrol.memory import Memory
from roomcontrol.smoke import SmokeManager, smoke_active
from roomcontrol.control import FullControl, _wanted

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def boot(d, area_name="Woonkamer", first=True):
    hass = HomeAssistant(d)
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    async def on(c):
        ids = c.data["entity_id"] if isinstance(c.data["entity_id"], list) else [c.data["entity_id"]]
        for e in ids:
            b = c.data.get("brightness") or (round(c.data["brightness_pct"] * 255 / 100) if "brightness_pct" in c.data else 255)
            hass.states.async_set(e, "on", {"brightness": b})
    async def off(c): pass
    hass.services.async_register("light", "turn_on", on); hass.services.async_register("light", "turn_off", off)
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    reg = ar.async_get(hass)
    a = reg.async_get_area_by_name(area_name) or reg.async_create(area_name)
    hass.states.async_set("light.bank", "on", {"brightness": 26 if not first else 200})
    room = {"area_id": a.id, "lights": [{"entity_id": "light.bank"}], "groups": [{"id": "g1", "lights": ["light.bank"], "dim": True}], "full_control": True}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {"dim_level": 10}, "entities": {}}
    mem = Memory(hass); await mem.async_load(); mem.start(); hass.data[DOMAIN]["memory"] = mem
    smoke = SmokeManager(hass); hass.data[DOMAIN]["smoke"] = smoke
    fc = FullControl(hass)
    e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_wk"; e._members = ["light.bank"]
    await e.async_added_to_hass()
    fc.start(); smoke.start()
    return hass, e, smoke, mem, fc

async def main():
    d = tempfile.mkdtemp()
    hass, e, smoke, mem, fc = await boot(d)
    await e.async_set_dim(True); await asyncio.sleep(0.2)
    e.async_set_manual(30)
    smoke.active = True; smoke.since = dt_util.utcnow(); smoke.areas = ["x"]; smoke._switches_were_on = ["switch.koffie"]
    _wanted(hass)["light.bank"] = {"on": True, "brightness": 26, "at": dt_util.utcnow()}
    e._dbg("on", "motion", ["light.bank"])
    await hass.async_stop()  # EVENT_HOMEASSISTANT_STOP → memory saved
    hass2, e2, smoke2, mem2, fc2 = await boot(d, first=False)
    await hass2.async_block_till_done()
    check("Dim kept", e2.dimmed, True)
    check("Dim brightness to return to kept", e2._dim_saved.get("light.bank"), 200)
    check("manual control kept (about 30 min left)", e2._manual_until is not None and 29*60 < (e2._manual_until - dt_util.utcnow()).total_seconds() <= 30*60, True)
    check("smoke still active until All safe", (smoke_active(hass2), smoke2.areas, smoke2._switches_were_on), (True, ["x"], ["switch.koffie"]))
    check("full control wanted kept", _wanted(hass2).get("light.bank", {}).get("brightness"), 26)
    check("debug log kept + restart note", [x["reason"] for x in e2.debug_log()][:2], ["restart", "motion"])
    smoke2.clear(); e2.async_set_manual(0)
    await hass2.async_stop()
    hass3, e3, smoke3, _, _ = await boot(d, first=False)
    check("after All safe + manual off: not kept", (smoke_active(hass3), e3._manual_until), (False, None))
    await hass3.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
