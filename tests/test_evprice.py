import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.ev as EV
from roomcontrol.const import DOMAIN
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    base = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    fc=[{"datetime": (base+timedelta(hours=i)).isoformat(), "electricity_price": int(0.35*1e7)} for i in range(12)]
    hass.states.async_set("sensor.zp", "3500000", {"forecast": fc})
    hass.data[DOMAIN] = {"settings": {"energy": {"price_sensor": "sensor.zp", "market_source": "fixed", "feed_in_kwh": 0.07}}}
    cfg={"price_sensor":"sensor.zp","charger_max_kw":3.7,"base_load_w":400}
    EV.sun_kw_at = lambda sun, s, e: 0.4 + 0.07*3.7  # 7 % of the charger from own sun, all day
    ps = EV.price_status(hass, cfg, {"soc": 49, "battery_kwh": 8.8}, [{"x": 1}])
    c = ps["cheapest"]; need = ps["kwh"]
    check("shown price is the tariff", c["avg"], 0.35)
    check("sun share", c["sun_pct"], 7)
    want = round((0.35*0.93 + 0.07*0.07) * need, 2)
    check("cost: grid at tariff + own sun at feed-in", c["cost"], want)
    check("charging now costs the same (same method)", c["cost_now"], want)
    no_feed = dict(hass.data[DOMAIN]["settings"]["energy"]); no_feed.pop("feed_in_kwh"); no_feed["market_source"]="fixed"
    full = EV.price_status(hass, cfg, {"soc": 100, "battery_kwh": 8.8}, [{"x": 1}])
    check("100 %: full, no cheapest", (full["full"], full["cheapest"], full["kwh"]), (True, None, 0.0))
    unknown = EV.price_status(hass, cfg, {"battery_kwh": 8.8})
    check("unknown soc: not full", unknown["full"], False)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
