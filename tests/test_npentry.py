import sys, types, tempfile, asyncio
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import roomcontrol.tariff as T, roomcontrol.nordpool_prices as NP
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); await er.async_load(hass)
    reg=er.async_get(hass)
    a=reg.async_get_or_create("sensor","nordpool","NL-current_price",suggested_object_id="np_nl")
    b=reg.async_get_or_create("sensor","nordpool","BE-current_price",suggested_object_id="np_be")
    # attach config entries (bypass validation)
    reg.entities[a.entity_id]=a.__class__(**{**{k:getattr(a,k) for k in a.__attrs_attrs__.__dict__ if not k.startswith('_')}, "config_entry_id":"e1"}) if False else a
    E={"market_source":"nordpool","market_entry":"e2"}; hass.data["roomcontrol"]={"settings":{"energy":E}}
    got=[]; NP.find_sensor=lambda h,entry_id=None: (got.append(entry_id), {"e1":a.entity_id,"e2":b.entity_id,None:a.entity_id}[entry_id])[1]
    check("service chosen → its sensor", (T.market_sensor(hass), got[-1]), (b.entity_id,"e2"))
    E.pop("market_entry"); check("no service chosen → first", (T.market_sensor(hass), got[-1]), (a.entity_id,None))
    E["market_source"]="auto"; check("auto → Nord Pool found", T.market_sensor(hass), a.entity_id)
    E["market_source"]="sensor"; E["market_sensor"]="sensor.entsoe"; check("other sensor", T.market_sensor(hass), "sensor.entsoe")
    E["market_source"]="derived"; check("derived → none", T.market_sensor(hass), None)
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
