"""Schemakeuze select: one per room with its own selector (room device) and one for the house (Generiek);
options are the schedule names, choosing one sets the input_number that RoomMind reads."""
import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from roomcontrol.const import DOMAIN, SIGNAL_CONFIG_UPDATED
import roomcontrol.select as SEL

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

class Entry:
    entry_id = "e1"
    def __init__(self): self.unloads = []
    def async_on_unload(self, f): self.unloads.append(f)

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    from homeassistant.helpers import entity_registry as er, device_registry as dr, area_registry as ar; await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass)
    calls = []
    async def set_value(call):
        calls.append((call.data["entity_id"], call.data["value"]))
        hass.states.async_set(call.data["entity_id"], str(float(call.data["value"])), {"min": 1, "max": 3})
    hass.services.async_register("input_number", "set_value", set_value)
    S = hass.states.async_set
    S("input_number.schemakeuze_woon", "1.0", {"min": 1, "max": 3}); S("input_number.schema_huis", "2.0", {"min": 1, "max": 3})
    S("schedule.a", "on", {"friendly_name": "Normaal"}); S("schedule.b", "off", {"friendly_name": "Armed Home"}); S("schedule.c", "off", {"friendly_name": "Normaal"})
    rooms = [{"area_id": "woon", "heating": {"selector": "input_number.schemakeuze_woon", "schedules": ["schedule.a", "schedule.b", "schedule.c"]}},
             {"area_id": "keuken", "heating": {"scope": "house"}}]
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {"heating": {"selector": "input_number.schema_huis", "names": {"1": "Normaal", "2": "Weg"}}}}
    added = []
    def add(ents, update=False, **kw):
        for e in ents:
            e.hass = hass; e.entity_id = f"select.t_{e.key.strip('_')}"; added.append(e)
    await SEL.async_setup_entry(hass, Entry(), add)
    for e in added: await e.async_added_to_hass()
    check("selects: room woon (own selector) and the house, not keuken", sorted(e.key for e in added), [SEL.HOUSE, "woon"])
    woon = next(e for e in added if e.key == "woon"); house = next(e for e in added if e.key == SEL.HOUSE)
    check("room options: schedule names, duplicates numbered", woon.options, ["Normaal", "Armed Home", "3 · Normaal"])
    check("room current: 1 → Normaal", woon.current_option, "Normaal")
    check("house options: general names", house.options, ["1 · Normaal", "2 · Weg", "3"])
    check("house current: 2", house.current_option, "2 · Weg")
    check("devices: room / Generiek", (woon.device_info["identifiers"], house.device_info["identifiers"]), ({(DOMAIN, "woon")}, {(DOMAIN, "general")}))
    await woon.async_select_option("Armed Home"); await hass.async_block_till_done()
    check("choose Armed Home: input_number to 2", calls[-1], ("input_number.schemakeuze_woon", 2))
    check("select follows the helper", woon.current_option, "Armed Home")
    S("input_number.schemakeuze_woon", "3.0", {"min": 1, "max": 3}); await hass.async_block_till_done()
    check("helper changed elsewhere (RoomMind): select follows", woon.current_option, "3 · Normaal")
    rooms[0]["heating"].pop("selector"); async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
    check("room selector removed: no room select wanted", "woon" in SEL.schedule_selectors(hass), False)
    await hass.async_stop()

asyncio.run(main())
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
