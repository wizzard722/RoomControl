import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.util import dt as dt_util
import roomcontrol.solar_forecast as SF
import roomcontrol.ev as EV
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.language="nl"
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize(); await hass.async_start()
    def mk(t, uid):
        e = config_entries.ConfigEntry(version=1, minor_version=1, domain="forecast_solar", title=t, data={}, source="user", options={}, unique_id=uid, discovery_keys={}, subentries_data=None)
        hass.config_entries._entries[e.entry_id] = e; return e.entry_id
    oost, west = mk("Dak oost","a"), mk("Dak west","b")
    base = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    async def get(h, eid):
        # 6 kWh/h from hour 3 to 5 on each roof
        return {"wh_hours": {(base+timedelta(hours=i)).isoformat(): (3000 if 3 <= i <= 5 else 0) for i in range(12)}}
    async def plats(h): return {"forecast_solar": get}
    SF._platforms = plats
    check("list", [f["title"] for f in await SF.async_list(hass)], ["Dak oost","Dak west"])
    wh = await SF.async_read(hass, [oost, west])
    sun = SF.periods(wh)
    check("two roofs added: 6 kW at hour 4", round(SF.sun_kw_at(sun, base+timedelta(hours=4), base+timedelta(hours=5)),1), 6.0)
    # prices: hour 4 expensive (0.35), hour 8 cheap (0.20)
    prices=[0.30]*12; prices[4]=0.35; prices[8]=0.20
    fc=[{"datetime": (base+timedelta(hours=i)).isoformat(), "electricity_price": int(p*1e7)} for i,p in enumerate(prices)]
    hass.states.async_set("sensor.zp", "3000000", {"forecast": fc})
    cfg={"price_sensor":"sensor.zp","charger_max_kw":3.7,"base_load_w":400}
    no_sun = EV.price_status(hass, cfg, {"soc": 60, "battery_kwh": 8.8})
    with_sun = EV.price_status(hass, cfg, {"soc": 60, "battery_kwh": 8.8}, sun)
    hr = lambda ps: (dt_util.parse_datetime(ps["cheapest"]["start"]) - base).seconds//3600
    check("without sun: hour 8 cheapest", hr(no_sun), 8)
    check("with sun: sunny hours win, 100% sun, free", (hr(with_sun) in (3,4,5), with_sun["cheapest"]["sun_pct"], with_sun["cheapest"]["cost"]), (True, 100, 0.0))
    check("forecast rows carry sun share", with_sun["forecast"][4-0 if dt_util.utcnow()<base+timedelta(hours=1) else 3]["sun_share"] if False else max(r["sun_share"] for r in with_sun["forecast"]), 1.0)
    check("grid share partial: 2 kW sun, 0.4 base, 3.7 charger", round(SF.grid_share(2.0,0.4,3.7),3), round(1-1.6/3.7,3))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
