import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.covers_known import CoverMemory
from roomcontrol.binary_sensor import CoversOpenSensor
from roomcontrol.entity_ids import _suggest

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    async def rec(c): pass
    for s in ("open_cover", "close_cover", "set_cover_position"): hass.services.async_register("cover", s, rec)
    a = ar.async_get(hass).async_create("Slaapkamer")
    hass.data[DOMAIN] = {"rooms": [{"area_id": a.id, "covers": ["cover.a", "cover.b"]}]}
    mem = CoverMemory(hass); await mem.async_load(); mem.start(); hass.data[DOMAIN]["cover_memory"] = mem
    hass.states.async_set("cover.a", "open", {}); hass.states.async_set("cover.b", "open", {})
    s = CoversOpenSensor(a.id); _suggest(hass, "binary_sensor", s)
    print("entity id:", s.entity_id, "| name:", s.name, "| device class:", s.device_class)
    s.hass = hass; s.entity_id = s.entity_id or "binary_sensor.x"
    s._refresh = s._refresh  # noqa
    from unittest.mock import patch
    with patch.object(type(s), "async_write_ha_state", lambda self: None):
        s._refresh(); check("device says open, never commanded: open", s.is_on, True)
        await hass.services.async_call("cover", "close_cover", {"entity_id": ["cover.a", "cover.b"]}, blocking=True); await hass.async_block_till_done(); s._refresh()
        check("RoomControl closed them: closed (device still says open)", (s.is_on, s.extra_state_attributes["state"]), (False, "closed"))
        await hass.services.async_call("cover", "set_cover_position", {"entity_id": "cover.a", "position": 30}, blocking=True); await hass.async_block_till_done(); s._refresh()
        check("one partly open: open", (s.is_on, s.extra_state_attributes["state"]), (True, "partly_open"))
    mem.stop(); await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
