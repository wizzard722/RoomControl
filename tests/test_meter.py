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

def status(house_w, keuken=2400, woon=400, consumed=None, produced=0, car=False):
    return {"configured": True, "phases": {"L1": house_w},
            "phase_detail": {"L1": {"consumed": house_w if consumed is None else consumed, "produced": produced, "solar": 500, "battery": None}},
            "rooms": {"keuken": {"phase": "L1", "watts": keuken, "parts": [{"key": "switch:switch.oven", "kind": "switch", "name": "Oven", "watts": keuken - 60}, {"key": "switch:switch.koel", "kind": "switch", "name": "Koelkast", "watts": 60}]},
                      "woonkamer": {"phase": "L1", "watts": woon, "parts": [{"key": "switch:switch.tv", "kind": "switch", "name": "Tv", "watts": woon}]}},
            "car": {"charging": car, "kw": 3.7 if car else 0, "phase": "L1", "name": "Audi"}}

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"energy": {"price_kwh": 0.30, "market_source": "fixed", "feed_in_kwh": 0.05, "fuse_a": 25, "charger_max_kw": 3.7}}}
    m = EM.EnergyMeter(hass)
    t = dt_util.as_utc(datetime(2026, 11, 25, 14, 0, tzinfo=dt_util.get_default_time_zone()))
    m.add(status(3500), t)
    for i in range(1, 121):  # one hour at 30 s
        m.add(status(3500), t + timedelta(seconds=30 * i))
    d = m.days["2026-11-25"]
    check("keuken 2.4 kWh", round(d["rooms"]["keuken"], 2), 2.4)
    check("house 3.5 kWh", round(d["house"], 2), 3.5)
    check("unassigned 0.7 kWh", round(d["unassigned"], 2), 0.7)
    check("cost keuken €0.72", round(d["rooms_cost"]["keuken"], 2), 0.72)
    check("grid in 3.5 · cost 1.05", (round(d["grid_in"], 2), round(d["cost_in"], 2)), (3.5, 1.05))
    check("solar 0.5", round(d["solar"], 2), 0.5)
    check("totals for sensor", round(m.totals["woonkamer"], 2), 0.4)
    # a gap (restart) is not counted
    m.add(status(3500), t + timedelta(hours=3))
    check("gap ignored", round(m.days["2026-11-25"]["house"], 2), 3.5)
    # nights: 03:00-05:00 base load
    for night in range(3):
        n0 = dt_util.as_utc(datetime(2026, 11, 20 + night, 3, 0, tzinfo=dt_util.get_default_time_zone()))
        m._last = None
        for i in range(0, 240):
            m.add(status(150, keuken=60, woon=14), n0 + timedelta(seconds=30 * i))
    with patch.object(EM.dt_util, "utcnow", return_value=t):
        b = m.base_load()
    check("base load 150 W, 3 nights", (b["watts"], b["nights"]), (150.0, 3))
    check("parts: koelkast 60, tv 14", [(p["name"], p["watts"]) for p in b["parts"]][:2], [("Koelkast", 60.0), ("Tv", 14.0)])
    check("unassigned at night", b["unassigned"], 76.0)
    # overview with warning: L1 at 3500 W ≈ 15 A + car 16 A > 25 A
    class E: last_status = status(3500)
    hass.data[DOMAIN]["energy"] = E()
    with patch.object(EM.dt_util, "utcnow", return_value=t + timedelta(minutes=61)):
        ov = m.overview()
    check("now", (ov["now"]["grid_w"], ov["now"]["house_w"], ov["now"]["unassigned_w"]), (3500, 3500, 700))
    check("phase amps", ov["phases"][0]["amps"], 15.2)
    check("warning car 16 A → 31 A", ov["warning"], {"phase": "L1", "car_a": 16, "total_a": 31})
    check("rooms sorted, top parts", (ov["rooms"][0]["area"], ov["rooms"][0]["top"][0]["name"], ov["rooms"][0]["kwh"]), ("keuken", "Oven", 2.4))
    check("base month €", ov["base"]["month"], round(150 / 1000 * 24 * 30 * 0.30, 2))
    check("today keys", sorted(ov["today"]), ["cost_in", "earn_out", "grid_in", "grid_out", "house", "house_cost", "solar", "unassigned"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
