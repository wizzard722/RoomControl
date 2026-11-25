import asyncio, sys, tempfile, types
from datetime import timedelta, datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol as RC
import roomcontrol.energy_meter as EM

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

class Light:
    def __init__(s): s._last_motion_at = dt_util.utcnow() - timedelta(hours=2); s._manual = False
    def _motion_sensors(s): return ["binary_sensor.pir"]
    def _any_motion(s): return False
    def _own_active(s): return []
    def _clock_lamps(s): return set()

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    rooms = [{"area_id": "woonkamer", "groups": [{"id": "g1", "name": "Leeslamp", "lights": ["light.lees"]}],
              "switches": [{"entity_id": "switch.tv", "off_on": ["all_off"]}]}]
    hass.states.async_set("person.p", "not_home")
    hass.data[DOMAIN] = {"rooms": rooms, "entities": {"woonkamer": Light()},
                         "settings": {"persons": ["person.p"], "energy": {"price_kwh": 0.30}}}
    m = EM.EnergyMeter(hass)
    status = {"configured": True, "phases": {"L1": 200}, "phase_detail": {"L1": {"consumed": 200, "produced": 0}},
              "rooms": {"woonkamer": {"phase": "L1", "watts": 54, "parts": [
                  {"key": "bundle:g1", "kind": "bundle", "name": "Leeslamp", "watts": 40},
                  {"key": "switch:switch.tv", "kind": "switch", "name": "Tv", "watts": 14}]}}, "car": {}}
    t = dt_util.utcnow().replace(microsecond=0)
    m.add(status, t)
    for i in range(1, 241):  # 2 hours
        m.add(status, t + timedelta(seconds=30 * i))
    day = m.days[dt_util.as_local(t + timedelta(hours=2)).strftime("%Y-%m-%d")] if dt_util.as_local(t + timedelta(hours=2)).date() == dt_util.as_local(t).date() else m.days[dt_util.as_local(t).strftime("%Y-%m-%d")]
    idle = day["idle"]["woonkamer|bundle:g1"]; away = day["away"]["woonkamer|switch:switch.tv"]
    check("idle 40 W × 2 h = 0.08 kWh, 1 episode", (round(idle["kwh"], 2), idle["n"]), (0.08, 1))
    check("away 14 W, 2 h", (round(away["h"], 1), round(away["w"])), (2.0, 14))
    # make it a week's worth: 5 episodes, 12 h away
    idle["n"] = 5; idle["eur"] = 0.3; away["h"] = 31; away["eur"] = 0.13
    c = m.coach()
    kinds = {x["kind"]: x for x in c["tips"]}
    check("tips: idle + away", sorted(kinds), ["away", "idle"])
    check("idle tip applies idle_off", kinds["idle"]["apply"], {"type": "bundle_idle_off", "area": "woonkamer", "group": "g1"})
    check("away tip applies nobody_home", kinds["away"]["apply"], {"type": "switch_nobody_home", "area": "woonkamer", "entity": "switch.tv"})
    saved = {}
    async def fake_save(h, rooms=None, settings=None):
        saved["rooms"] = rooms; h.data[DOMAIN]["rooms"] = rooms
    with patch.object(RC, "_async_save", fake_save):
        r1 = await m.async_apply("idle|woonkamer|bundle:g1")
        r2 = await m.async_apply("away|woonkamer|switch:switch.tv")
    room = hass.data[DOMAIN]["rooms"][0]
    check("applied", (r1, r2), (True, True))
    check("bundle idle_off set", room["groups"][0].get("idle_off"), True)
    check("tv off when nobody home, back on", (room["switches"][0]["off_on"], room["switches"][0]["back_on"]), (["all_off", "nobody_home"], True))
    c2 = m.coach()
    check("after apply: no apply offered any more", [x["apply"] for x in c2["tips"]], [None, None])
    m.dismiss("idle|woonkamer|bundle:g1")
    check("dismissed hidden", [x["kind"] for x in m.coach()["tips"]], ["away"])
    check("rooms cost list", [r["area"] for r in c["rooms"]][:1], ["woonkamer"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
