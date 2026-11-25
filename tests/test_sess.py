import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers import area_registry as ar
import roomcontrol.energy as E
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    d = tempfile.mkdtemp(); hass = HomeAssistant(d); hass.config.language="nl"; await ar.async_load(hass); await hass.async_start()
    hass.data["roomcontrol"]={"rooms":[],"settings":{"energy":{"phase_sensors":{"L1":"sensor.l1"},"charger_room":"x","soc_sensor":"sensor.soc","battery_kwh":10,"price_kwh":0.25,"charge_from_kw":1.2}}}
    S=hass.states.async_set
    en=E.Energy(hass); await en.async_load()
    t=[dt_util.utcnow()]
    E.dt_util.utcnow = lambda: t[0]
    def step(w, soc, mins=30):
        S("sensor.l1", str(w), {"unit_of_measurement":"W"}); S("sensor.soc", str(soc), {"unit_of_measurement":"%"})
        en._tick(); t[0]=t[0]+timedelta(minutes=mins)
    # Charging counts after CHARGE_CONFIRM (90 s) over the limit: a 2-minute step first.
    step(100, 50); step(3700, 50, mins=2); step(3700, 50); step(3700, 60); step(3700, 70); step(3700, 80); step(100, 80); 
    h = en.history()
    s = h["sessions"][0]
    check("session kWh (3 × 30 min × 3.7 kW)", s["kwh"], 5.55)
    check("into battery = 30% × 10 kWh", s["battery_kwh"], 3.0)
    check("cost 5.55 × 0.25", s["cost"], 1.39)
    check("month totals", (h["month"]["count"], h["month"]["kwh"], h["month"]["cost"]), (1, 5.5, 1.39))
    await hass.async_block_till_done(); await en._store._async_handle_write_data() if hasattr(en._store,'_async_handle_write_data') else None
    # restart while charging
    step(3700, 82, mins=2); step(3700, 82); step(3700, 84)
    en2 = E.Energy(hass); await en2._store.async_save(en._store._data["data"] if isinstance(en._store._data, dict) and "data" in en._store._data else {"sessions": en.sessions, "current": {"since": en.charging_since.isoformat(), "kwh": en.charged_kwh, "cost": en.cost, "priced": True, "soc_from": en.soc_from}})
    en3 = E.Energy(hass); await en3.async_load()
    check("resumed session after restart", (en3.charging_since == en.charging_since, round(en3.charged_kwh,2), len(en3.sessions)), (True, 1.85, 1))
    hass.data["roomcontrol"]["settings"]["energy"]["history_days"]=1
    en3.sessions[0]["end"]=(dt_util.utcnow()-timedelta(days=3)).isoformat(); en3._prune()
    check("old session pruned after history_days", len(en3.sessions), 0)
    # solar: 3 phases, house returns 2 kW net in the first half hour, imports 1 kW in the second
    en4 = E.Energy(hass); en4.sessions=[]
    cfg = hass.data["roomcontrol"]["settings"]["energy"]
    cfg.update({"has_solar": True, "produced_sensors": {"L1": "sensor.back"}, "price_kwh": 0.30})
    def step2(used, back, soc):
        S("sensor.l1", str(used), {"unit_of_measurement":"W"}); S("sensor.back", str(back), {"unit_of_measurement":"W"}); S("sensor.soc", str(soc), {"unit_of_measurement":"%"})
        en4._tick(); t[0]=t[0]+timedelta(minutes=30)
    # charger estimate = phase net (used - back + 0 solar) ... use a charging sensor to force charging at max kw
    S("binary_sensor.ch","on"); cfg["charging_sensor"]="binary_sensor.ch"; cfg["charger_max_kw"]=3.7
    step2(4000, 6000, 50); step2(4000, 6000, 60); step2(4700, 3700, 70)
    S("binary_sensor.ch","off"); step2(100, 0, 70)
    s2 = en4.sessions[-1]
    check("solar part (first half hour all own power)", (s2["solar_kwh"], s2["grid_kwh"]), (1.85+1.35, 0.5))
    check("cost only for grid part", s2["cost"], round(0.5*0.30, 2))
    from roomcontrol.tariff import sell_now
    sell = sell_now(hass) or 0.0
    check("saved = sun part × (price − feed-in price)", s2["saved"], round(3.2 * (0.30 - sell), 2))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
