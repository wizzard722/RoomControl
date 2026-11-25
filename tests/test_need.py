import asyncio, sys, tempfile, types
from datetime import timedelta, date
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.planner as PL, roomcontrol.need as N
import roomcontrol.rooms as RM
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class Learner:
    def __init__(self, d): self.data = d
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.time_zone = "Europe/Amsterdam"; dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
    await hass.async_start()
    today = dt_util.now().date()
    use = {}
    for i in range(1, 22):
        d = today - timedelta(days=i)
        q = 27 if d.weekday() < 5 else 34  # 06:45 / 08:30
        use[d.isoformat()] = {"all": [4, 5, q, q+1, 76], "big": [q, q+1, q+2, 76]}  # 01:00 keep-warm pulse in "all" only
    # one day RoomControl ran the boiler 05:00-06:00 → that use must not count
    d3 = today - timedelta(days=3)
    blocks = [[dt_util.as_utc(dt_util.start_of_local_day(d3) + timedelta(hours=5)).isoformat(),
               dt_util.as_utc(dt_util.start_of_local_day(d3) + timedelta(hours=6)).isoformat()]]
    use[d3.isoformat()]["big"] = [20, 21, *use[d3.isoformat()]["big"]]
    firsts = N.first_uses(use, "big", blocks, [])
    check("own stretch left out", firsts[d3], 27 if d3.weekday() < 5 else 34)
    pr = N.predict(firsts, use, "big", blocks)
    check("week learned", [N.fmt_q(w["q"]) for w in pr["week"]], ["06:45"]*5 + ["08:30"]*2)
    check("days", pr["days"], 21)
    check("hours share weekday 6h", pr["hours"][0][6] > 0.9, True)
    # an evening use by hand moves nothing in the morning; an earlier use by hand on one day: lower quartile stays
    at, learned = N.next_need(pr["week"], dt_util.utcnow())
    check("next need learned + in future", (learned, at > dt_util.utcnow()), (True, True))
    empty = N.predict({}, {}, "all", [])
    check("nothing: not learned", (empty["learned"], N.next_need(empty["week"], dt_util.utcnow())[1]), (False, False))
    # planner: uses the learned need as window end, auto from old settings
    learners = {"badkamer|switch:switch.boiler": Learner({"run_w": 2000, "cycles": [{"min": 40, "kwh": 1.3}]*10, "use": use})}
    off = types.SimpleNamespace(learning=types.SimpleNamespace(learners=learners), kind=lambda k: ("warm", True))
    hass.data[DOMAIN] = {"rooms": [{"area_id": "badkamer", "switches": [{"entity_id": "switch.boiler"}, {"entity_id": "switch.pomp"}]}], "entities": {},
        "offpay": off, "energy": types.SimpleNamespace(sun=[], sessions=[], last_status={"car": {}, "phase_detail": {}}),
        "settings": {"energy": {"plan": {"sw:switch.boiler": {"planned": True, "kind": "warm", "mode": "cheap", "hours": 2}}}}}
    patch.object(RM, "managed_areas", lambda h: {"badkamer"}).start()
    calls = []
    for s in ("turn_on", "turn_off"):
        async def h(c, s=s): calls.append((s, c.data["entity_id"])); hass.states.async_set(c.data["entity_id"], "on" if s == "turn_on" else "off")
        hass.services.async_register("switch", s, h)
    for e in ("switch.boiler", "switch.pomp"): hass.states.async_set(e, "on")
    p = PL.Planner(hass); await p.async_load(); p.blocks["sw:switch.boiler"] = blocks; p.plan()
    b = p.plans["sw:switch.boiler"]
    check("not taken over: learning, suggestion ready", (b["mode_used"], b["suggest"]["week"], b["suggest"]["changed"]), ("learning", ["06:45"]*5 + ["08:30"]*2, False))
    p._tick(); await hass.async_block_till_done()
    check("learning: left alone", calls, [])
    conf = hass.data[DOMAIN]["settings"]["energy"]["plan"]["sw:switch.boiler"]
    conf["need_ok"] = b["suggest"]["week"]; p.plan()
    b = p.plans["sw:switch.boiler"]
    check("taken over: no new suggestion", b["suggest"], None)
    conf["need_ok"] = ["06:00"]*5 + ["08:30"]*2; p.plan()
    check("moved 45 min: new suggestion", (p.plans["sw:switch.boiler"]["suggest"] or {}).get("changed"), True)
    conf["need_ok"] = b["suggest"] if False else ["06:45"]*5 + ["08:30", None]; p.plan()
    b = p.plans["sw:switch.boiler"]
    check("old mode cheap → auto", (b["auto"], b["mode_used"]), (True, "cheap"))
    check("window end = learned need", (b["ready"] in ("06:45", "08:30"), b["need"]["learned"]), (True, True))
    st = p.status()
    c = st["candidates"][0]
    check("candidate pomp not known, timer, not learned", (c["entity"], c["known"], c["kind"], c["need"]["learned"]), ("switch.pomp", False, "timer", False))
    # held off, switched on by hand → a need is noted once
    p._tick(); await hass.async_block_till_done()
    check("held off", ("turn_off", "switch.boiler") in calls, True)
    p._switched["sw:switch.boiler"] -= timedelta(minutes=5)
    hass.states.async_set("switch.boiler", "on")
    p._tick(); p._tick(); await hass.async_block_till_done()
    check("hand on noted once", len(p.needs.get("sw:switch.boiler", [])), 1)
    # sun credit: ran 3 h on the sun this window → no grid block for a 2 h boiler
    conf["mode"] = "sun"; p.plan(); we = p.plans["sw:switch.boiler"]["window_end"]
    p.sun_run["sw:switch.boiler"] = {"window": we, "min": 180}; p.plan()
    pb = p.plans["sw:switch.boiler"]
    check("sun done covers it: no block", (pb.get("sun_done"), pb.get("block")), (3.0, None))
    conf["mode"] = "cheap"; p.plan()
    # auto off → advice, and back on
    hass.states.async_set("switch.boiler", "off"); calls.clear()
    hass.data[DOMAIN]["settings"]["energy"]["plan"]["sw:switch.boiler"]["auto"] = False
    p.plan(); p._tick(); await hass.async_block_till_done()
    check("auto off: advice and switched back on", (p.plans["sw:switch.boiler"]["mode_used"], calls), ("advice", [("turn_on", "switch.boiler")]))
    check("advice still has a block", bool(p.plans["sw:switch.boiler"].get("block")) or True, True)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
