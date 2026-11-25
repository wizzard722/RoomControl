"""Energy → Overzicht 2: kWh per hour, per part (minutes on, switch-ons), filling hours from statistics, overview2()."""
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

def status(house_w, tv=100, lamp=0, produced=0, solar=0):
    return {"configured": True, "phases": {"L1": house_w},
            "phase_detail": {"L1": {"consumed": house_w, "produced": produced, "solar": solar, "battery": None}},
            "rooms": {"woon": {"phase": "L1", "watts": tv + lamp, "parts": [
                {"key": "switch:switch.tv", "kind": "switch", "name": "Tv", "watts": tv},
                {"key": "bundle:1", "kind": "bundle", "name": "Plafond", "watts": lamp}]}},
            "car": {}}

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"energy": {"price_kwh": 0.30, "market_source": "fixed"}}}
    m = EM.EnergyMeter(hass)
    tz = dt_util.get_default_time_zone()
    t = dt_util.as_utc(datetime(2026, 11, 25, 10, 0, tzinfo=tz))
    m.add(status(1000), t)
    for i in range(1, 121):  # 10:00-11:00, lamp on 10:00-10:30, off, on again 10:45
        lamp = 50 if i <= 60 or i > 90 else 0
        m.add(status(1000, lamp=lamp, solar=400, produced=100), t + timedelta(seconds=30 * i))
    d = m.days["2026-11-25"]
    h = d["hours"]
    check("hours 10+11 house 1 kWh (last tick is 11:00)", round(h["house"][10] + h["house"][11], 2), 1.0)
    check("hour 10 solar 0.4, out 0.1", (round(h["solar"][10], 2), round(h["grid_out"][10], 2)), (0.4, 0.1))
    check("other hours empty", sum(h["house"][:10]), 0.0)
    p = d["parts"]["woon|bundle:1"]
    check("lamp minutes on 45", round(p["min"]), 45)
    check("lamp went on twice", p["n"], 2)
    check("tv on 60 min, once", (round(d["parts"]["woon|switch:switch.tv"]["min"]), d["parts"]["woon|switch:switch.tv"]["n"]), (60, 1))
    # filling from statistics: hours 0-9 not counted, hour 10 counted (kept)
    per = {"grid_in": [0.3] * 24, "grid_out": [0.0] * 24, "solar": [0.0] * 24}
    per["solar"][9] = 0.5; per["grid_out"][9] = 0.1
    m.fill_hours("2026-11-25", per, set(range(0, 11)), 11)
    check("filled 0-9", d["filled"], list(range(10)))
    check("hour 9 house = in + sun - out", round(h["house"][9], 2), 0.7)
    check("counted hour 10 kept", round(h["house"][10], 2), 0.99)
    # yesterday for comparison
    y = m.days.setdefault("2026-11-24", {"rooms": {}, "rooms_cost": {}})
    y["house"] = 20.0; y["hours"] = {"house": [0.5] * 24}
    hass.data[DOMAIN]["energy"] = types.SimpleNamespace(last_status=status(1000, lamp=50, tv=100))
    with patch.object(EM.dt_util, "utcnow", return_value=t + timedelta(hours=1, minutes=30)):
        o = m.overview2()
    check("hour/minute", (o["hour"], o["minute"]), (11, 30))
    check("yesterday up to 11:30 = 5.75", o["yesterday"]["house_upto"], 5.75)
    check("parts sorted by kWh", [x["name"] for x in o["parts"]], ["Tv", "Plafond"])
    check("live now, biggest first", [(x["name"], x["watts"]) for x in o["live"]], [("Tv", 100), ("Plafond", 50)])
    # older days lose hours/parts at the hourly clean-up
    old = m.days.setdefault("2026-11-10", {"rooms": {}, "rooms_cost": {}, "hours": {"house": [0] * 24}, "parts": {"x": {}}})
    m.add(status(1000), dt_util.as_utc(datetime(2026, 11, 25, 12, 0, 0, tzinfo=tz)) - timedelta(seconds=30))
    m.add(status(1000), dt_util.as_utc(datetime(2026, 11, 25, 12, 0, 0, tzinfo=tz)))
    check("old day keeps totals but not hours/parts", ("hours" in old, "parts" in old), (False, False))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
