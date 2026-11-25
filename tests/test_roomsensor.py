import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from roomcontrol.const import DOMAIN, SIGNAL_CONFIG_UPDATED
from homeassistant.helpers.dispatcher import async_dispatcher_send
import roomcontrol.sensor as S
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    a = ar.async_get(hass).async_create("Keuken")
    hass.data[DOMAIN] = {"rooms": [{"area_id": a.id, "lights": [{"entity_id": "light.x"}]}], "settings": {"energy": {"phase_sensors": {"L1": "sensor.l1"}}},
                         "meter": types.SimpleNamespace(totals={a.id: 3.14159})}
    added = []
    class Entry:
        def async_on_unload(self, f): pass
    with __import__("unittest.mock").mock.patch.object(S, "with_roomcontrol_ids", lambda h, d, f: f), __import__("unittest.mock").mock.patch.object(S, "managed_areas", lambda h: {a.id}):
        await S.async_setup_entry(hass, Entry(), lambda ents: added.extend(ents))
        ens = [e for e in added if isinstance(e, S.RoomEnergySensor)]
        print("energy sensors:", [e.unique_id for e in ens])
        e = ens[0]; e.hass = hass; e._refresh(); print("value:", e.native_value, e.device_class, e.state_class, e.native_unit_of_measurement)
        hass.data[DOMAIN]["settings"]["energy_enabled"] = False
        await hass.async_stop()
asyncio.run(main())
