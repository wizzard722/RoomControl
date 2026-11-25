import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize()
    await hass.async_start()
    entry = config_entries.ConfigEntry(version=1, minor_version=1, domain="wled", title="WLED", data={}, source="user", options={}, unique_id="w1", discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    dev = dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={("wled", "d")}, name="Strip voordeur")
    reg = er.async_get(hass)
    reg.async_get_or_create("light", "wled", "l", suggested_object_id="strip_voordeur", device_id=dev.id, config_entry=entry)
    reg.async_get_or_create("select", "wled", "p", suggested_object_id="strip_voordeur_preset", device_id=dev.id, config_entry=entry, translation_key="preset")
    calls = []
    for dom, svc in (("light","turn_on"),("light","turn_off"),("select","select_option")):
        async def h(c, d=dom, s=svc): calls.append((d, s, dict(c.data)))
        hass.services.async_register(dom, svc, h)
    P = "alarm_control_panel.x"; hass.states.async_set(P, "disarmed")
    hass.data[DOMAIN] = {"rooms": [], "settings": {"alarm_entity": P, "alarm": {"slots_on": False, "states": {
        "armed_away": {"lamps": [{"entity_id": "light.strip_voordeur", "preset": "Armed Away"}, {"entity_id": "light.hal"}]},
        "armed_home": {"lamps": [{"entity_id": "light.strip_voordeur", "preset": "Armed Home"}]},
        "disarmed": {"lamps": [{"entity_id": "light.strip_voordeur"}]}}}}}
    a = A.AlarmAutomation(hass); a.start(); await hass.async_block_till_done()
    check("preset select found", a.preset_select("light.strip_voordeur"), "select.strip_voordeur_preset")
    hass.states.async_set(P, "armed_away"); await hass.async_block_till_done()
    pick = lambda: [(c[0], c[1], c[2].get("entity_id"), c[2].get("option")) for c in calls]
    check("armed away: preset + other lamp on", pick(), [("select","select_option","select.strip_voordeur_preset","Armed Away"),("light","turn_on","light.hal",None)])
    calls.clear(); hass.states.async_set(P, "armed_home"); await hass.async_block_till_done()
    check("armed home: hal off, strip preset", pick(), [("light","turn_off",["light.hal"],None),("select","select_option","select.strip_voordeur_preset","Armed Home")])
    calls.clear(); hass.states.async_set(P, "disarmed"); await hass.async_block_till_done()
    check("disarmed: strip on without preset", pick(), [("light","turn_on","light.strip_voordeur",None)])
    a.stop(); await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
