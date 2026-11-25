import asyncio, sys, tempfile, types, random
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.predict as PR, roomcontrol.rooms as RM
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class FakeLight:
    def __init__(self): self.motion = False; self._members = ["light.k"]; self._last_motion_at = dt_util.utcnow(); self._session_start = None
    def _own_motion(self): return self.motion
    def _media_active(self): return False
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.time_zone = "Europe/Amsterdam"; dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
    await hass.async_start()
    L = FakeLight()
    hass.data[DOMAIN] = {"rooms": [{"area_id": "keuken"}], "entities": {"keuken": L}, "settings": {"persons": ["person.paul"]}}
    patch.object(RM, "managed_areas", lambda h: {"keuken"}).start()
    p = PR.Predictor(hass)
    start = dt_util.start_of_local_day() - timedelta(days=10)
    clock = {"t": dt_util.as_utc(start)}
    patch.object(PR.dt_util, "utcnow", lambda: clock["t"]).start()
    random.seed(1)
    for minute in range(10 * 1440):
        t = dt_util.as_utc(start + timedelta(minutes=minute)); clock["t"] = t
        loc = dt_util.as_local(t); h = loc.hour + loc.minute / 60; wd = loc.weekday() < 5
        home = not (wd and 8.5 <= h < 17.5)
        hass.states.async_set("person.paul", "home" if home else "not_home")
        use = home and ((wd and 7 <= h < 8) or 18 <= h < 20 or (not wd and 9 <= h < 11))
        L.motion = use and random.random() < 0.6
        if L.motion: L._last_motion_at = t
        hass.states.async_set("light.k", "on" if use else "off")
        p._tick()
    r = p.rooms["keuken"]
    print("samples", r.now.n, "days", r.days())
    # predict for a weekday 18:30 with Paul home, and 03:00
    def at(day_off, hh, mm, home, motion, lamps):
        t = dt_util.as_utc(dt_util.start_of_local_day() + timedelta(days=day_off, hours=hh, minutes=mm)); clock["t"] = t
        hass.states.async_set("person.paul", "home" if home else "not_home")
        L.motion = motion; L._last_motion_at = t if motion else t - timedelta(hours=5)
        hass.states.async_set("light.k", "on" if lamps else "off")
        return p.status("keuken")
    # find next weekday
    d = 0
    while (dt_util.start_of_local_day() + timedelta(days=d)).weekday() >= 5: d += 1
    s1 = at(d, 18, 30, True, True, True); s2 = at(d, 3, 0, True, False, False); s3 = at(d, 17, 55, True, False, False)
    print("18:30 in use:", s1["p_now"], "03:00:", s2["p_now"], "17:55 before:", s3["p_now"], "certainty:", s1["certainty"])
    check("18:30 in use high", s1["p_now"] >= 80, True)
    check("03:00 low", s2["p_now"] <= 10, True)
    check("17:55 rising", s3["p_now"] > s2["p_now"], True)
    check("certainty good", (s1["certainty"] or 0) >= 75, True)
    check("timeline 96 and evening high", (len(s1["timeline"]), s1["timeline"][18*4+2] > 50, s1["timeline"][3*4] < 15), (96, True, True))
    print("why:", s1["why"][:4]); print("tl", s1["timeline"][::4]); print({k:v for k,v in p.rooms["keuken"].day.w.items() if "slot:wd:3" in k or k in ("dark","person:person.paul","nobody")}, p.rooms["keuken"].day.b)
    check("why has items", len(s1["why"]) > 0, True)
    check("not ready (10 days)", p.ready("keuken"), False)
    r.first = (dt_util.as_local(dt_util.utcnow()).date() - timedelta(days=15)).isoformat()
    check("ready after 14 days", p.ready("keuken"), True)
    s4 = at(d, 17, 30, True, False, False)
    ev = p.upcoming("keuken")
    print("upcoming", ev)
    check("upcoming: start soon", bool(ev) and ev[0]["kind"] == "pred_start", True)
    check("replay at 18:30 yes, 03:00 no", (p.replay_want("keuken", dt_util.as_utc(dt_util.start_of_local_day() + timedelta(days=d, hours=18, minutes=30))),
                                            p.replay_want("keuken", dt_util.as_utc(dt_util.start_of_local_day() + timedelta(days=d, hours=3)))), (True, False))
    c = p.chance_now("keuken"); check("chance_now works", c is not None, True)
    hass.data[DOMAIN]["rooms"][0]["predict"] = {"skip": ["person.paul"]}
    st = p.status("keuken"); check("skip person: not a feature", any(w.get("kind") == "person" for w in st["why"]), False)
    p.forget("keuken"); check("forget", "keuken" in p.rooms, False)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
