import asyncio, sys, tempfile, types
from datetime import datetime, timedelta, timezone
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.ev as EV
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
rows_src = [  # from the user's sensor (amounts in 1/10,000,000 €)
 ("2026-11-19T16:00:00+01:00","2026-11-19T16:15:00+01:00",4115185,3006704),
 ("2026-11-19T16:15:00+01:00","2026-11-19T16:30:00+01:00",4181977,3073496),
 ("2026-11-20T01:00:00+01:00","2026-11-20T01:15:00+01:00",3155050,2046569),
 ("2026-11-20T01:15:00+01:00","2026-11-20T01:30:00+01:00",3295168,2186687),
 ("2026-11-20T06:00:00+01:00","2026-11-20T06:15:00+01:00",3244469,2135988),
]
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    fc=[{"start_date":a,"end_date":b,"price_tax_included":{"amount":i},"price_tax_excluded":{"amount":x},"sustainability_score":{"permille":200}} for a,b,i,x in rows_src]
    hass.states.async_set("sensor.zonneplan_current_quarter_hourly_electricity_tariff","0.4115",{"forecast":fc,"unit_of_measurement":"€/kWh"})
    rows = EV.price_forecast(hass,"sensor.zonneplan_current_quarter_hourly_electricity_tariff")
    check("5 rows, tax included in €", [round(r["price"],4) for r in rows], [0.4115,0.4182,0.3155,0.3295,0.3244])
    check("ends from end_date (15 min; no 1-hour gap fill)", [(r["end"]-r["start"]).seconds//60 for r in rows], [15,15,15,15,15])
    now = datetime(2026,11,19,15,5,tzinfo=timezone.utc)  # 16:05 local
    best = EV.cheapest(rows, 0.25, now=now)
    check("cheapest quarter = 01:00 local", best["start"].strftime("%H:%M UTC") if best else None, "00:00 UTC")
    best = EV.cheapest(rows, 0.5, now=now)
    check("30 min: 01:00-01:30 (06:00 alone is too short)", best["start"].strftime("%H:%M UTC") if best else None, "00:00 UTC")
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
