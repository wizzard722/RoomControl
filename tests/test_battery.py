import asyncio, sys, tempfile, types, time
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.battery as B

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

def day_hours(start, days):
    out = []
    for d in range(days):
        for h in range(24):
            t = start + timedelta(days=d, hours=h)
            lt = dt_util.as_local(t).hour
            imp = 0.8 if lt in (7, 8, 18, 19, 20, 21) else 0.3
            exp = 1.5 if 11 <= lt <= 15 else 0.0
            if exp: imp = 0.0
            buy = 0.15 if lt < 6 else 0.42 if lt in (7, 8, 18, 19, 20) else 0.25
            out.append({"t": t, "imp": imp, "exp": exp, "buy": buy, "sell": buy / 1.21 - 0.13})
    return out

class Energy:
    sun = []; last_status = {"car": {"charging": False}, "phase_detail": {"L1": {"consumed": 900, "produced": 0}}}

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    start = dt_util.as_utc(dt_util.start_of_local_day() - timedelta(days=7))
    hours = day_hours(start, 7)
    p = B.params({})
    check("params: low = reserve 20% of 5 kWh", (round(p["low"], 2), p["high"]), (1.0, 5.0))
    t0 = time.time(); r = B.simulate(hours, p); dt = time.time() - t0
    print("sim", r, f"{dt:.2f}s")
    check("price ≤ self ≤ none", r["price"] <= r["self"] + 1e-6 and r["self"] <= r["none"], True)
    check("battery saves", r["none"] - r["price"] > 0.5, True)
    r2 = B.simulate(hours, p, grid_charge=False)
    check("no grid charge: not better than with", r2["price"] >= r["price"] - 1e-6, True)
    big = B.params({}, 10, 3.6); rb = B.simulate(hours, big)
    check("10 kWh saves at least as much", (r["none"] - rb["price"]) >= (r["none"] - r["price"]) - 0.01, True)
    _c, _e, flows, path = B.optimise([(x["imp"] - x["exp"], x["buy"], x["sell"]) for x in hours[:24]], p, 1.0, p["low"])
    check("never below reserve", min(path) >= p["low"] - 1e-9, True)
    check("power limit", max(abs(f) for f in flows) <= p["max_charge_kw"] / p["eta"] + 1e-6, True)
    # 90 days speed
    t0 = time.time(); B.simulate(day_hours(start - timedelta(days=83), 90), big); print(f"90 days 10 kWh: {time.time()-t0:.1f}s")
    # control
    calls = []
    async def setv(c): calls.append(("number", c.data["value"]))
    async def sel(c): calls.append(("select", c.data["option"]))
    hass.services.async_register("number", "set_value", setv); hass.services.async_register("select", "select_option", sel)
    base = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    prices = [0.30] * 30; prices[2] = 0.08; prices[3] = 0.08; prices[6] = 0.55; prices[7] = 0.55
    fc = [{"datetime": (base + timedelta(hours=i)).isoformat(), "electricity_price": int(v * 1e7)} for i, v in enumerate(prices)]
    hass.states.async_set("sensor.zp", "3000000", {"forecast": fc})
    hass.states.async_set("sensor.bat_soc", "40"); hass.states.async_set("sensor.bat_w", "0", {"unit_of_measurement": "W"})
    hass.states.async_set("number.bat", "0", {"min": -2400, "max": 2400})
    hass.data[DOMAIN] = {"energy": Energy(), "settings": {"energy": {"price_sensor": "sensor.zp", "market_source": "fixed", "feed_in_kwh": 0.05,
        "battery": {"soc_sensor": "sensor.bat_soc", "power_sensor": "sensor.bat_w", "control": "number", "number_entity": "number.bat",
                    "strategy": "price", "grid_charge": True, "capacity_kwh": 5}}}}
    hb = B.HomeBattery(hass); await hb.async_load()
    hb.profile = {str(h): 0.4 for h in range(24)}
    hb.make_plan()
    acts = {}
    for q in hb.plan:
        hr = int((dt_util.parse_datetime(q["start"]) - base).total_seconds() // 3600)
        acts.setdefault(hr, set()).add(q["action"])
    print("plan by hour:", {h: sorted(a) for h, a in sorted(acts.items()) if h < 10})
    check("charges in the cheap hours 2-3", "charge" in acts.get(2, set()) | acts.get(3, set()), True)
    check("not discharging before the dear hours (idle or self)", "charge" not in acts.get(5, set()), True)
    blocks = hb.blocks(); print("blocks:", [(b["action"], b["start"][11:16], b["end"][11:16], b["kwh"]) for b in blocks][:6])
    check("blocks have prices", all("price" in b for b in blocks), True)
    # tick: in a quarter → sends a command (number signed)
    t_cheap = next(dt_util.parse_datetime(q["start"]) for q in hb.plan if q["action"] == "charge") + timedelta(minutes=1)
    with patch.object(B.dt_util, "utcnow", return_value=t_cheap):
        hb._planned_at = t_cheap; hb._tick(); await hass.async_block_till_done()
    check("cheap hour: charge with + W", calls and calls[-1][0] == "number" and calls[-1][1] > 0, True)
    calls.clear()
    with patch.object(B.dt_util, "utcnow", return_value=t_cheap + timedelta(minutes=1)):
        hb._tick(); await hass.async_block_till_done()
    check("same action: no new command", calls, [])
    # car charging, not to_car → idle 0 in a self quarter
    hass.data[DOMAIN]["energy"].last_status = {"car": {"charging": True}, "phase_detail": {"L1": {"consumed": 4000, "produced": 0}}}
    t_self = next(dt_util.parse_datetime(q["start"]) for q in hb.plan if q["action"] == "self" and dt_util.parse_datetime(q["start"]) > t_cheap)
    with patch.object(B.dt_util, "utcnow", return_value=t_self + timedelta(minutes=1)):
        hb._planned_at = t_self; hb._tick(); await hass.async_block_till_done()
    check("car charging: battery holds (0 W)", calls[-1] if calls else None, ("number", 0))
    # test button
    calls.clear(); await hb.async_test("discharge", 500); await hass.async_block_till_done()
    check("test discharge 500 → −500", calls, [("number", -500)])
    # measure: discharging 1 kW for 6 min while importing at 0.30 → about +0.03 €
    hass.states.async_set("sensor.bat_w", "-1000", {"unit_of_measurement": "W"})
    hb._last = dt_util.utcnow() - timedelta(minutes=6); hb._measure(dt_util.utcnow())
    m = list(hb.months.values())[0]
    check("measured value ≈ 0.1 kWh × 0.30 − wear", round(m, 3), round(0.1 * 0.30 - 0.1 * 0.03, 3))
    # simulation via async_hours with mocked statistics
    hass.data[DOMAIN]["settings"]["energy"].update({"phase_sensors": {"L1": "sensor.l1"}, "produced_sensors": {"L1": "sensor.r1"}})
    hass.states.async_set("sensor.l1", "500", {"unit_of_measurement": "W"}); hass.states.async_set("sensor.r1", "0", {"unit_of_measurement": "W"})
    hrs = day_hours(start, 7)
    async def fake_stats(h, ids, s, e, kind):
        if kind == "mean":
            return {"sensor.l1": [{"start": x["t"].timestamp(), "mean": x["imp"] * 1000} for x in hrs],
                    "sensor.r1": [{"start": x["t"].timestamp(), "mean": x["exp"] * 1000} for x in hrs]}
        return {"sensor.grid_in": [{"start": x["t"].timestamp(), "change": x["imp"] * 1.03} for x in hrs],
                "sensor.grid_out": [{"start": x["t"].timestamp(), "change": x["exp"]} for x in hrs]}
    async def fake_dash(h): return ["sensor.grid_in"], ["sensor.grid_out"]
    with patch.object(B, "_stats", fake_stats), patch.object(B, "_dashboard_grid", fake_dash):
        sim = await hb.async_simulate(7, [{"kwh": 5, "kw": 2.4, "price": 3000}, {"kwh": 10, "kw": 3.6}])
    print("sim meta:", {k: sim[k] for k in ("source", "match", "days", "priced_pct")})
    check("source roomcontrol, match ~98%", (sim["source"], 95 <= (sim["match"] or 0) <= 100), ("roomcontrol", True))
    check("rows with savings + payback", (len(sim["rows"]), sim["rows"][0]["year_price"] > 0, sim["rows"][0]["payback"] is not None), (2, True, True))
    st = hb.status()
    check("status keys", sorted(k for k in st if k in ("configured", "soc", "plan", "blocks", "sim", "month")), ["blocks", "configured", "month", "plan", "sim", "soc"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
