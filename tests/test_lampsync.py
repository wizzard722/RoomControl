import asyncio, sys, tempfile, types, copy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN
from roomcontrol.lamp_sync import LampSync
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {})
    await hass.config_entries.async_initialize()
    await hass.async_start()
    entry = config_entries.ConfigEntry(version=1, minor_version=1, domain="hue", title="Hue", data={}, source="user", options={}, unique_id="hue1", discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    areg, ereg, dreg = ar.async_get(hass), er.async_get(hass), dr.async_get(hass)
    wk, hal, zolder = areg.async_create("Woonkamer"), areg.async_create("Hal"), areg.async_create("Zolder")
    dev = dreg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("hue", "d1")}, name="Spots")
    dreg.async_update_device(dev.id, area_id=wk.id)
    e1 = ereg.async_get_or_create("light", "hue", "l1", suggested_object_id="plafond", device_id=dev.id)  # area via device
    e2 = ereg.async_get_or_create("light", "hue", "l2", suggested_object_id="leeslamp"); ereg.async_update_entity(e2.entity_id, area_id=wk.id)
    e3 = ereg.async_get_or_create("light", "hue", "l3", suggested_object_id="staande"); ereg.async_update_entity(e3.entity_id, area_id=wk.id)
    e4 = ereg.async_get_or_create("light", "hue", "l4", suggested_object_id="tafel"); ereg.async_update_entity(e4.entity_id, area_id=wk.id)
    hass.states.async_set("light.yaml_lamp", "off")  # no registry entry
    rooms = [{"area_id": wk.id, "lights": [{"entity_id": e} for e in ("light.plafond","light.leeslamp","light.staande","light.tafel","light.yaml_lamp")],
              "groups": [{"id": "g1", "name": "Plafond", "lights": ["light.plafond", "light.leeslamp"]}]},
             {"area_id": hal.id, "lights": [], "groups": []}]
    saves = []
    async def save(h, r): saves.append(copy.deepcopy(r)); h.data[DOMAIN]["rooms"] = r
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {}}
    ls = LampSync(hass, save)
    moves = await ls.async_sync()
    check("start: nothing to do (all in their area, YAML lamp kept)", moves, [])
    ls.start()
    R = lambda: hass.data[DOMAIN]["rooms"]
    lamps = lambda i: [l["entity_id"] for l in R()[i]["lights"]]
    # 1. lamp moved to Hal (room) via entity area
    ereg.async_update_entity("light.leeslamp", area_id=hal.id); await hass.async_block_till_done()
    m = await ls.async_sync()
    check("leeslamp moved to Hal", (m, "light.leeslamp" in lamps(0), lamps(1), R()[0]["groups"][0]["lights"]), ([("light.leeslamp", wk.id, hal.id)], False, ["light.leeslamp"], ["light.plafond"]))
    # 2. device moved to Zolder (not a RoomControl room)
    dreg.async_update_device(dev.id, area_id=zolder.id); await hass.async_block_till_done()
    m = await ls.async_sync()
    check("plafond (device) moved to Zolder: leaves room, group empty", (m, "light.plafond" in lamps(0), R()[0]["groups"][0]["lights"]), ([("light.plafond", wk.id, zolder.id)], False, []))
    # 3. lamp taken out of any area
    ereg.async_update_entity("light.staande", area_id=None); await hass.async_block_till_done()
    m = await ls.async_sync()
    check("staande without area leaves room", (m, "light.staande" in lamps(0)), ([("light.staande", wk.id, None)], False))
    # 4. rename
    ereg.async_update_entity("light.tafel", new_entity_id="light.eettafel"); await hass.async_block_till_done()
    m = await ls.async_sync()
    check("renamed lamp keeps its place", lamps(0), ["light.eettafel", "light.yaml_lamp"])
    # 5. removed from HA
    ereg.async_remove("light.eettafel"); await hass.async_block_till_done()
    m = await ls.async_sync()
    check("removed lamp leaves room", (m, lamps(0)), ([("light.eettafel", wk.id, None)], ["light.yaml_lamp"]))
    check("YAML lamp untouched", "light.yaml_lamp" in lamps(0), True)
    # 6. events schedule a sync by themselves (debounce 1 s)
    ereg.async_update_entity("light.leeslamp", area_id=wk.id); await hass.async_block_till_done()
    await asyncio.sleep(1.3); await hass.async_block_till_done()
    check("event-driven: leeslamp back in Woonkamer", (lamps(0), lamps(1)), (["light.yaml_lamp", "light.leeslamp"], []))
    ls.stop(); await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
