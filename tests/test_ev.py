import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.ev as EV
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.language = "nl"; await hass.async_start()
    base = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    prices = [0.30,0.28,0.25,0.10,0.08,0.09,0.20,0.35,0.40,0.12,0.11,0.30]
    fc = [{"datetime": (base+timedelta(hours=i)).isoformat(), "electricity_price": int(p*1e7), "tariff_group":"normal"} for i,p in enumerate(prices)]
    hass.states.async_set("sensor.zonneplan_current_electricity_tariff", str(int(0.30*1e7)), {"forecast": fc})
    rows = EV.price_forecast(hass, "sensor.zonneplan_current_electricity_tariff")
    check("zonneplan rows scaled to €", (len(rows), round(rows[3]["price"],2), rows[0]["end"]-rows[0]["start"]), (12, 0.10, timedelta(hours=1)))
    best = EV.cheapest(rows, 2, now=base)
    check("cheapest 2 h = hours 4-5", ((best["start"]-base).seconds//3600, round(best["avg"],3)), (4, 0.085))
    best = EV.cheapest(rows, 3, now=base)
    check("cheapest 3 h = hours 3-5", ((best["start"]-base).seconds//3600, round(best["avg"],3)), (3, 0.09))
    best = EV.cheapest(rows, 1.5, now=base, ready_by=base+timedelta(hours=3))
    check("ready by +3h: only first 3 hours", ((best["start"]-base).seconds/3600, (best["end"]-base).seconds/3600), (1.5, 3.0))
    check("too long → None", EV.cheapest(rows, 20, now=base), None)
    # Nord Pool style, ct/kWh
    hass.states.async_set("sensor.np", "25", {"raw_today": [{"start": (base+timedelta(hours=i)).isoformat(), "end": (base+timedelta(hours=i+1)).isoformat(), "value": p*100} for i,p in enumerate(prices)]})
    check("nordpool ct → €", round(EV.price_forecast(hass, "sensor.np")[4]["price"],2), 0.08)
    cfg = {"price_sensor": "sensor.zonneplan_current_electricity_tariff", "charger_max_kw": 3.7}
    ps = EV.price_status(hass, cfg, {"soc": 50, "battery_kwh": 8.8})
    check("price status hours (4.4 kWh / 3.7 kW)", (ps["hours"], ps["found"], ps["cheapest"] is not None), (1.19, True, True))
    check("render", EV.render(hass, EV.event_cfg(hass, cfg, "cheap")["text"], {"name": "Audi"}, ps).startswith("De goedkoopste tijd om Audi te laden begint nu ("), True)
    # notifier
    sent = []
    async def fake(h, c, m, test=False): sent.append(m); return {}
    EV.async_send = fake
    n = EV.EvNotifier(hass); cfg2 = {}
    car = lambda ch, kwh=None, soc=None: {"name": "", "charging": ch, "kw": 3.6 if ch else 0, "charged_kwh": kwh, "soc": soc}
    for c in [car(False), car(True), car(False), car(True), car(True, 1.0), car(True, 2.5), car(False), car(False, None, 60)]:
        n.update(cfg2, c, None); await hass.async_block_till_done()
    check("messages: start once after 2 checks, stop with kWh", sent, ["De auto is begonnen met laden (3,6 kW).", "De auto is gestopt met laden. Er is 2,5 kWh geladen."])
    sent.clear(); n.update(cfg2, car(True), None); n.update(cfg2, car(True), None); n.update(cfg2, car(False, None, 99), None); n.update(cfg2, car(False, None, 99), None); await hass.async_block_till_done()
    check("full at 99%", sent[-1], "De auto is vol geladen.")
    cfg3 = {"notify": {"events": {"started": {"on": False}}}}; sent.clear()
    n2 = EV.EvNotifier(hass)
    for c in [car(False), car(True), car(True)]: n2.update(cfg3, c, None)
    await hass.async_block_till_done(); check("started off → no message", sent, [])
    # 15-minute prices: cheapest 45 minutes must be the three cheap quarters
    q=[0.30]*8+[0.05,0.06,0.04]+[0.30]*20
    fcq=[{"datetime": (base+timedelta(minutes=15*i)).isoformat(), "electricity_price": int(p*1e7)} for i,p in enumerate(q)]
    hass.states.async_set("sensor.zp15", "3000000", {"forecast": fcq})
    rq = EV.price_forecast(hass, "sensor.zp15")
    check("15-min rows end after 15 min", rq[0]["end"]-rq[0]["start"], timedelta(minutes=15))
    bq = EV.cheapest(rq, 0.75, now=base)
    check("cheapest 45 min = quarters 8-10", ((bq["start"]-base).seconds//60, (bq["end"]-base).seconds//60, round(bq["avg"],3)), (120, 165, 0.05))
    psq = EV.price_status(hass, {"price_sensor": "sensor.zp15", "charger_max_kw": 3.7}, {"soc": 50, "battery_kwh": 8.8})
    check("forecast: the quarters not yet past (27-31)", 27 <= len(psq["forecast"]) <= 31, True)
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
