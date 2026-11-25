import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
import roomcontrol.tariff as T
import roomcontrol.nordpool_prices as NP
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await er.async_load(hass); await hass.async_start()
    S=hass.states.async_set
    n0=dt_util.utcnow(); now=n0.replace(minute=n0.minute//15*15,second=0,microsecond=0); q=lambda i:(now+timedelta(minutes=15*i)).isoformat()
    S("sensor.zonneplan","0.24",{"forecast":[{"start_date":q(i),"end_date":q(i+1),"price_tax_included":{"amount":2400000}} for i in range(8)]})
    E={"price_sensor":"sensor.zonneplan"}; hass.data["roomcontrol"]={"settings":{"energy":E}}
    check("before Nord Pool: derived", T.status(hass)["market_source"], "derived")
    # built-in Nord Pool installed later
    reg=er.async_get(hass)
    e=reg.async_get_or_create("sensor","nordpool","NL-current_price",config_entry=None, suggested_object_id="nord_pool_nl_current_price")
    S(e.entity_id,"0.072",{"unit_of_measurement":"EUR/kWh"})
    st=T.status(hass); check("found automatically, price now only", (st["market_source"], st["market"], st["market_sensor"], st["market_periods"]), ("market_sensor", 0.072, e.entity_id, 1))
    # fake the built-in service
    calls=[]
    async def svc(call):
        calls.append(dict(call.data)); return {"NL":[{"start":q(i),"end":q(i+1),"price":65.0+i} for i in range(8)]}
    hass.services.async_register("nordpool","get_prices_for_date",svc,supports_response=SupportsResponse.ONLY)
    reg.async_update_entity(e.entity_id, config_entry_id=None)
    NP._entry=lambda h,s: types.SimpleNamespace(config_entry_id="cfg1", unique_id="NL-current_price", platform="nordpool") if s==e.entity_id else None
    np=NP.NordPoolPrices(hass); np.start(); await hass.async_block_till_done(); await asyncio.sleep(0.05)
    st=T.status(hass); check("forecast fetched via action (MWh→kWh)", (st["market_periods"] >= 7, st["market"], calls[0]["areas"]), (True, 0.065, ["NL"]))
    # HACS Nord Pool
    S("sensor.nordpool_hacs","0.08",{"raw_today":[{"start":q(i),"end":q(i+1),"value":0.08} for i in range(8)]})
    E["market_sensor"]="sensor.nordpool_hacs"; st=T.status(hass)
    check("HACS sensor chosen", (st["market_sensor"], st["market"], st["market_periods"]>=7), ("sensor.nordpool_hacs", 0.08, True))
    np.shutdown(); await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
