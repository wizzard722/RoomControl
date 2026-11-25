import asyncio, sys, tempfile, types
from datetime import timedelta, datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.energy_meter as EM

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"energy": {"bill": {"termijn": 95, "fixed_month": 30, "gas_price": 1.25}}}}
    m = EM.EnergyMeter(hass)
    now = dt_util.as_utc(datetime(2026, 11, 25, 12, 0, tzinfo=dt_util.get_default_time_zone()))
    for d in range(1, 26):
        m.days[f"2026-11-{d:02d}"] = {"cost_in": 2.0, "earn_out": 0.2, "grid_in": 8, "grid_out": 1}
    for d in range(10, 32):
        m.days[f"2026-10-{d:02d}"] = {"cost_in": 1.5, "earn_out": 0.0, "grid_in": 6, "grid_out": 0}
    async def gas(start, end):
        days = {}
        t = dt_util.as_local(start)
        while t < dt_util.as_local(end):
            days[t.strftime("%Y-%m-%d")] = 1.0
            t += timedelta(days=1)
        return days, True
    with patch.object(EM.dt_util, "utcnow", return_value=now), patch.object(m, "_gas_days", gas):
        b = await m.async_bill()
        o = await m.async_bill("2026-10")
    check("upto 25 of 30", (b["upto"], b["days"]), (25, 30))
    check("elec so far 25 × 1.80", b["elec"], 45.0)
    check("gas 25 m³ × 1.25", (b["gas_m3"], b["gas"]), (25.0, 31.25))
    check("fixed 25/30 × 30", b["fixed"], 25.0)
    check("total", b["total"], 101.25)
    # forecast: per day 1.80 + 1.25 = 3.05; left 5 days + half of today; fixed 5 more
    check("forecast", b["forecast"], round(101.25 + 3.05 * 5.5 + 5.0, 2))
    check("diff vs termijn 95", b["diff"], round(b["forecast"] - 95, 2))
    check("months list", b["months"], ["2026-10", "2026-11"])
    check("since", b["since"], "2026-10-10")
    check("october: whole month, no forecast", (o["current"], "forecast" in o, o["upto"]), (False, False, 31))
    check("october total", o["total"], round(22 * 1.5 + 31 * 1.25 + 30, 2))
    check("rows mark future days", sum(1 for r in b["rows"] if r["future"]), 5)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
