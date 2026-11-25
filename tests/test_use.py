import asyncio, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.planner as PL, roomcontrol.rooms as RM, roomcontrol.switch as SW
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class Learner:
    def __init__(self, d): self.data = d
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.time_zone = "Europe/Amsterdam"; dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
    await hass.async_start()
    patch.object(SW, "_sun_phase", lambda h: ("light", False)).start()
    today = dt_util.now().date()
    # coffee maker: used 07:00-07:15 and 12:30-12:45 every day, runs of 5 min, 3 a day
    use = {}; cycles = []
    for i in range(1, 22):
        d = today - timedelta(days=i)
        use[d.isoformat()] = {"all": [28, 50], "big": [28, 50], "e": [28, 50]}
        for h in (7, 12, 15):
            cycles.append({"start": dt_util.as_utc(dt_util.start_of_local_day(d) + timedelta(hours=h)).isoformat(), "min": 5, "kwh": 0.05})
    learners = {"keuken|switch:switch.koffie": Learner({"run_w": 1200, "cycles": cycles, "use": use, "hours": {}})}
    class Off:
        learning = types.SimpleNamespace(learners=learners)
        def kind(self, k): return ("task", True)
        hass = None
    hass.data[DOMAIN] = {"rooms": [{"area_id": "keuken", "switches": [{"entity_id": "switch.koffie"}]}], "entities": {},
        "offpay": Off(), "energy": types.SimpleNamespace(sun=[], sessions=[], last_status={"car": {}, "phase_detail": {}}),
        "settings": {"energy": {"plan": {}}}}
    patch.object(RM, "managed_areas", lambda h: {"keuken"}).start()
    calls = []
    for s in ("turn_on", "turn_off"):
        async def h(c, s=s): calls.append((s, c.data["entity_id"])); hass.states.async_set(c.data["entity_id"], "on" if s == "turn_on" else "off")
        hass.services.async_register("switch", s, h)
    hass.states.async_set("switch.koffie", "on")
    p = PL.Planner(hass); await p.async_load()
    st = p.status()
    c = st["candidates"][0]
    check("candidate guessed use", c["kind"], "use")
    check("proposal has 2 windows a day", len(c["proposal"]) >= 2 and all(x["start"]["type"] == "time" for x in c["proposal"]), True)
    print("  proposal:", [(x["days"], x["start"]["time"], x["end"]["time"]) for x in c["proposal"]])
    # planned with no slots: advice, nothing switched
    hass.data[DOMAIN]["settings"]["energy"]["plan"]["sw:switch.koffie"] = {"planned": True, "kind": "use", "auto": True}
    p.plan(); p._tick(); await hass.async_block_till_done()
    check("no slots: advice, not switched", (p.plans["sw:switch.koffie"]["mode_used"], calls), ("advice", []))
    # slot now → on; slot later → off; lead brings it on early
    loc = dt_util.now()
    hm = lambda t: t.strftime("%H:%M")
    slot = lambda a, b: {"days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": hm(a)}, "end": {"type": "time", "time": hm(b)}}
    conf = hass.data[DOMAIN]["settings"]["energy"]["plan"]["sw:switch.koffie"]
    conf["slots"] = [slot(loc + timedelta(hours=2), loc + timedelta(hours=3))]
    p.plan(); p._tick(); await hass.async_block_till_done()
    pl = p.plans["sw:switch.koffie"]
    check("slot later: use, off now", (pl["mode_used"], calls), ("use", [("turn_off", "switch.koffie")]))
    check("next block ~2h ahead", 1.7 < (dt_util.parse_datetime(pl["block"]["start"]) - dt_util.utcnow()).total_seconds() / 3600 <= 2.09, True)
    calls.clear(); conf["lead"] = 150; p.plan(); p._tick(); await hass.async_block_till_done()
    check("lead 150 min: on now", calls, [("turn_on", "switch.koffie")])
    calls.clear(); conf["lead"] = 0; conf["auto"] = False; p.plan(); p._tick(); await hass.async_block_till_done()
    check("auto off: advice", p.plans["sw:switch.koffie"]["mode_used"], "advice")
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
