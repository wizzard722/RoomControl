import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.control import rc_call, _matches
from roomcontrol.covers_known import CoverMemory, known_cover, known_covers
from roomcontrol.sensor import CoversStateSensor

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    d = tempfile.mkdtemp(); hass = HomeAssistant(d); await hass.async_start()
    async def rec(c): pass
    for s in ("open_cover", "close_cover", "set_cover_position", "stop_cover", "toggle"):
        hass.services.async_register("cover", s, rec)
    hass.data[DOMAIN] = {"rooms": [{"area_id": "slk", "covers": ["cover.inv", "cover.norm"], "covers_inverted": ["cover.inv"]}]}
    mem = CoverMemory(hass); await mem.async_load(); mem.start(); hass.data[DOMAIN]["cover_memory"] = mem
    hass.states.async_set("cover.inv", "open", {}); hass.states.async_set("cover.norm", "open", {"current_position": 37})
    check("before any command: device", (known_cover(hass,"cover.norm")["state"], known_cover(hass,"cover.norm")["source"]), ("partly_open","device"))
    await rc_call(hass, "cover", "close_cover", {"entity_id": ["cover.inv", "cover.norm"]}); await hass.async_block_till_done()
    check("RoomControl close (reversed gets open, known closed)", [known_cover(hass,e)["state"] for e in ("cover.inv","cover.norm")], ["closed","closed"])
    hass.states.async_set("cover.norm", "open", {"current_position": 100}); await hass.async_block_till_done()
    check("wrong device state ignored", known_cover(hass,"cover.norm")["state"], "closed")
    check("full control: matches known (no fight)", _matches(hass, hass.states.get("cover.norm"), {"cover":"closed"}), True)
    await hass.services.async_call("cover", "open_cover", {"entity_id": "cover.norm"}, blocking=True); await hass.async_block_till_done()
    check("other app opens: known open", known_cover(hass,"cover.norm")["state"], "open")
    check("full control sees deviation", _matches(hass, hass.states.get("cover.norm"), {"cover":"closed"}), False)
    await hass.services.async_call("cover", "set_cover_position", {"entity_id": ["cover.inv"], "position": 40}, blocking=True); await hass.async_block_till_done()
    check("position", known_cover(hass,"cover.inv"), {"state":"partly_open","position":40,"source":"roomcontrol"})
    check("room together", {k: v for k, v in known_covers(hass, ["cover.inv","cover.norm"]).items() if k != "covers"}, {"state":"partly_open","position":70})
    await hass.services.async_call("cover", "stop_cover", {"entity_id": "cover.norm"}, blocking=True); await hass.async_block_till_done()
    check("stop soon after: partly", known_cover(hass,"cover.norm")["state"], "partly_open")
    await hass.services.async_call("cover", "toggle", {"entity_id": "cover.norm"}, blocking=True); await hass.async_block_till_done()
    check("toggle from partly: closed", known_cover(hass,"cover.norm")["state"], "closed")
    s = CoversStateSensor("slk"); s.hass = hass; s._refresh()
    check("sensor", (s.native_value, s.extra_state_attributes["position"]), ("partly_open", 20))
    await mem._store.async_save({"covers": mem.known})
    mem2 = CoverMemory(hass); await mem2.async_load()
    check("kept after restart", mem2.known["cover.inv"]["position"], 40)
    mem.stop(); await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
