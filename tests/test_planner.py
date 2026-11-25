import asyncio, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.planner as PL
import roomcontrol.rooms as RM
PL_managed = lambda h: {"badkamer", "keuken"}

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

class Learner:
    def __init__(self, d): self.data = d
class Learning:
    def __init__(self): 
        self.learners = {"badkamer|switch:switch.boiler": Learner({"run_w": 2000, "cycles": [{"min": 40, "kwh": 1.3}]*10}),
                         "keuken|switch:switch.vaat": Learner({"run_w": 900, "cycles": [{"min": 150, "kwh": 1.1}]*6})}
        self.names = {"badkamer|switch:switch.boiler": "Boiler", "keuken|switch:switch.vaat": "Vaatwasser"}
class Offpay:
    def __init__(self): self.learning = Learning()
    def switches(self): return {"badkamer|switch:switch.boiler": "switch.boiler", "keuken|switch:switch.vaat": "switch.vaat"}
    def kind(self, k): return ("warm" if "boiler" in k else "task"), False
class Energy:
    sun = []; sessions = [{"kwh": 4.0}, {"kwh": 5.0}, {"kwh": 4.5}]
    last_status = {"car": {"charging": False}, "phase_detail": {"L1": {"consumed": 300, "produced": 0}}}

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.time_zone = "Europe/Amsterdam"; dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
    await hass.async_start()
    calls = []
    for d in ("switch",):
        for s in ("turn_on", "turn_off"):
            async def h(c, s=s): calls.append((s, c.data["entity_id"])); hass.states.async_set(c.data["entity_id"], "on" if s == "turn_on" else "off")
            hass.services.async_register(d, s, h)
    for e in ("switch.lader", "switch.boiler", "switch.vaat"): hass.states.async_set(e, "on")
    now = dt_util.utcnow().replace(second=0, microsecond=0)
    base = now.replace(minute=0)
    # prices per hour for 30 h: cheapest at hours 3-4 from now, co2 lowest at hours 10-11
    prices = [0.30]*30; prices[3] = 0.10; prices[4] = 0.12; prices[10] = 0.28
    fc = [{"datetime": (base + timedelta(hours=i)).isoformat(), "electricity_price": int(p*1e7)} for i, p in enumerate(prices)]
    hass.states.async_set("sensor.zp", "3000000", {"forecast": fc})
    co2 = [{"datetime": (base + timedelta(hours=i)).isoformat(), "carbon_intensity": (80 if i in (10, 11) else 400)} for i in range(30)]
    hass.states.async_set("sensor.co2", "350", {"forecast": co2, "unit_of_measurement": "gCO2eq/kWh"})
    ready = dt_util.as_local(base + timedelta(hours=20)).strftime("%H:%M")
    hass.data[DOMAIN] = {"rooms": [{"area_id": "badkamer", "switches": [{"entity_id": "switch.boiler"}]},
                                   {"area_id": "keuken", "switches": [{"entity_id": "switch.vaat"}, {"entity_id": "switch.tv"}, {"entity_id": "switch.koel", "may_off": False}]}], "entities": {},
        "offpay": Offpay(), "energy": Energy(),
        "settings": {"energy": {"price_sensor": "sensor.zp", "charger_room": "tuin", "charger_entity": "switch.lader", "charger_max_kw": 3.7,
                                "co2_sensor": "sensor.co2",
                                "plan": {"car": {"mode": "cheap", "ready": ready}, "sw:switch.boiler": {"planned": True, "kind": "warm", "mode": "cheap", "ready": ready, "hours": 2, "need_ok": [ready]*7},
                                         "sw:switch.vaat": {"planned": True, "kind": "task", "need_ok": [ready]*7}}}}}
    patch.object(RM, "managed_areas", PL_managed).start()
    p = PL.Planner(hass); await p.async_load(); p.plan()
    car, boiler, vaat = p.plans["car"], p.plans["sw:switch.boiler"], p.plans["sw:switch.vaat"]
    hrs = lambda pl: (round((dt_util.parse_datetime(pl["block"]["start"]) - base).total_seconds()/3600, 2), round((dt_util.parse_datetime(pl["block"]["end"]) - base).total_seconds()/3600, 2))
    check("car kwh from sessions median", car["device"]["kwh"], 4.5)
    check("car block in cheap hours 3-4.x", hrs(car)[0] >= 3 and hrs(car)[0] < 4, True)
    check("boiler 2h block starts at 3", hrs(boiler), (3.0, 5.0))
    check("dishwasher advice only (auto off)", (vaat["mode_used"], vaat["auto"], 2.5 <= hrs(vaat)[0] <= 3.0), ("advice", False, True))
    # CO2
    hass.data[DOMAIN]["settings"]["energy"]["plan_on"] = "co2"; p.plan()
    check("co2: boiler at the clean hours 10-12", hrs(p.plans["sw:switch.boiler"]), (10.0, 12.0))
    hass.data[DOMAIN]["settings"]["energy"]["plan_on"] = "price"; p.plan()
    # switching: before the block → off; in the block → on; after → off + run noted
    p._tick(); await hass.async_block_till_done()
    check("before block: charger + boiler off", sorted(c for c in calls), [("turn_off", "switch.boiler"), ("turn_off", "switch.lader")])
    check("dishwasher never switched", any(c[1] == "switch.vaat" for c in calls), False)
    calls.clear()
    t_in = base + timedelta(hours=3, minutes=20)
    with patch.object(PL.dt_util, "utcnow", return_value=t_in):
        p._tick(); await hass.async_block_till_done()
    check("in block: both on", sorted(calls), [("turn_on", "switch.boiler"), ("turn_on", "switch.lader")])
    calls.clear()
    # switched off by hand in the block: left alone
    hass.states.async_set("switch.boiler", "off")
    with patch.object(PL.dt_util, "utcnow", return_value=t_in + timedelta(minutes=10)):
        p._tick(); await hass.async_block_till_done()
    check("by hand in block: left alone", calls, [])
    # car still charging at the end of its block: it finishes
    p.hass.data[DOMAIN]["energy"].last_status = {"car": {"charging": True}, "phase_detail": {}}
    t_out = base + timedelta(hours=6)
    with patch.object(PL.dt_util, "utcnow", return_value=t_out):
        p._tick(); await hass.async_block_till_done()
    check("after: boiler off, car finishes", sorted(calls), [("turn_off", "switch.boiler")])
    check("runs noted, done", (len(p.runs), sorted(p.done)), (2, ["car", "sw:switch.boiler"]))
    calls.clear()
    p.hass.data[DOMAIN]["energy"].last_status = {"car": {"charging": False}, "phase_detail": {}}
    with patch.object(PL.dt_util, "utcnow", return_value=t_out + timedelta(minutes=5)):
        p._tick(); await hass.async_block_till_done()
    check("car done charging: off", calls, [("turn_off", "switch.lader")])
    st = p.status()
    check("status: rows ~96, savings", (len(st["rows"]) >= 95, st["savings"]["runs"] >= 0), (True, True))
    check("status devices", sorted(d["key"] for d in st["devices"]), ["car", "sw:switch.boiler", "sw:switch.vaat"])
    check("candidates: tv only (koelkast may not go off)", [c["entity"] for c in st["candidates"]], ["switch.tv"])
    check("boiler power learned 2 kW", next(d for d in st["devices"] if d["key"] == "sw:switch.boiler")["kw"], 2.0)
    # sun mode
    hass.data[DOMAIN]["settings"]["energy"]["plan"]["sw:switch.boiler"] = {"planned": True, "kind": "warm", "mode": "sun", "need_ok": [ready]*7}
    p.done.clear(); p._running.clear(); p._want.clear(); p._switched.clear(); p.plan(); calls.clear()
    p.hass.data[DOMAIN]["energy"].last_status = {"car": {}, "phase_detail": {"L1": {"consumed": 200, "produced": 1500}}}
    hass.states.async_set("switch.boiler", "off")
    p._tick(); await hass.async_block_till_done()
    check("sun: 1.3 kW surplus ≥ half of 2 kW → on", ("turn_on", "switch.boiler") in calls, True)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
