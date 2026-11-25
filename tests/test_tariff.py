import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.tariff as T
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    n0=dt_util.utcnow(); now=n0.replace(minute=n0.minute//15*15,second=0,microsecond=0)
    q=lambda i: (now+timedelta(minutes=15*i)).isoformat()
    rows=[{"start_date":q(i),"end_date":q(i+1),"price_tax_included":{"amount":2400000+i*10000},"price_tax_excluded":{"amount":600000}} for i in range(8)]
    hass.states.async_set("sensor.zonneplan","0.24",{"forecast":rows,"unit_of_measurement":"€/kWh"})
    E={"price_sensor":"sensor.zonneplan"}; hass.data["roomcontrol"]={"settings":{"energy":E}}
    st=T.status(hass); check("auto from Zonneplan excl. tax", (st["buy"], st["market"], st["sell"], st["market_source"]), (0.24, 0.06, 0.06, "price_sensor"))
    E["feed_in_cost_kwh"]=0.01; check("with cost", T.status(hass)["sell"], 0.05); E.pop("feed_in_cost_kwh")
    # no excl field → derived
    hass.states.async_set("sensor.zonneplan","0.24",{"forecast":[{k:v for k,v in r.items() if k!="price_tax_excluded"} for r in rows]})
    E.update(energy_tax_kwh=0.1, buy_markup_kwh=0.02)
    st=T.status(hass); check("derived", (st["market_source"], round(st["sell"],4)), ("derived", round(0.24/1.21-0.12,4)))
    # market sensor (Nord Pool)
    hass.states.async_set("sensor.nordpool","0.07",{"raw_today":[{"start":q(i),"end":q(i+1),"value":0.07} for i in range(8)]})
    E["market_sensor"]="sensor.nordpool"; check("nord pool", T.status(hass)["market_source"], "market_sensor")
    E["market_source"]="fixed"; E["feed_in_kwh"]=0.08; check("fixed", (T.status(hass)["sell"], T.status(hass)["market_source"]), (0.08,"fixed"))
    f=T.forecast(hass); check("forecast rows", (len(f) >= 7, f[0]["buy"]), (True, 0.24))
    E.clear(); E["price_kwh"]=0.3; st=T.status(hass); check("fixed buy contract", (st["buy"], st["buy_source"]), (0.3,"fixed"))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
