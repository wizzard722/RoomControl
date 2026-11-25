import asyncio, sys, tempfile, types
from datetime import datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
P = "alarm_control_panel.alarmo"
ALL = [0,1,2,3,4,5,6]
SLOTS = [{"name": "Nacht", "days": ALL, "start": {"type": "time", "time": "23:30"}, "end": {"type": "time", "time": "06:30"}, "state": "armed_home"},
         {"name": "Avond", "days": ALL, "start": {"type": "dusk"}, "end": {"type": "time", "time": "23:30"}, "state": "armed_home"},
         {"name": "Weg", "days": ALL, "start": {"type": "time", "time": "09:00"}, "end": {"type": "time", "time": "12:00"}, "state": "armed_away", "only_away": True}]
def short(u): return [(dt_util.parse_datetime(e["at"]).strftime("%d %H:%M"), e["kind"], e["name"], e["state"]) for e in u]
async def run(home, extra=None):
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    for svc in A.SERVICE_FOR:
        async def h(c, st=svc): hass.states.async_set(P, st)
        hass.services.async_register("alarm_control_panel", A.SERVICE_FOR[svc], h)
    tz = dt_util.DEFAULT_TIME_ZONE
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 10, "next_dusk": datetime(2026,11,20,17,30,tzinfo=tz).isoformat(), "next_setting": datetime(2026,11,20,17,0,tzinfo=tz).isoformat(), "next_rising": datetime(2026,11,21,8,0,tzinfo=tz).isoformat()})
    hass.states.async_set("person.paul", "home" if home else "not_home")
    hass.data[DOMAIN] = {"settings": {"alarm_entity": P, "alarm": {"slots": SLOTS, **(extra or {})}}, "rooms": []}
    now = datetime(2026, 11, 20, 8, 0, tzinfo=tz)
    with patch.object(A.dt_util, "now", side_effect=lambda: now):
        hass.states.async_set(P, "disarmed")
        a = A.AlarmAutomation(hass); a.start(); await hass.async_block_till_done()
        up = a.upcoming(); st = a.status()
        a.stop()
    await hass.async_stop()
    return up, st
async def main():
    up, st = await run(True)
    print(short(up))
    check("someone home: Weg (only away) skipped", any(e["name"] == "Weg" for e in up), False)
    check("Avond start at dusk 17:30", ("20 17:30", "slot_start", "Avond", "armed_home") in short(up), True)
    check("Avond end 23:30 dropped (Nacht starts)", any(e[1] == "slot_end" and e[2] == "Avond" for e in short(up)), False)
    check("Nacht start 23:30", ("20 23:30", "slot_start", "Nacht", "armed_home") in short(up), True)
    check("Nacht end 06:30 → disarmed", ("21 06:30", "slot_end", "Nacht", "disarmed") in short(up), True)
    check("sorted", [e["at"] for e in up] == sorted(e["at"] for e in up), True)
    check("in status", st["upcoming"] == up, True)
    up, _ = await run(False)
    print(short(up))
    check("nobody home: Weg start", ("20 09:00", "slot_start", "Weg", "armed_away") in short(up), True)
    check("nobody home: Weg end → away target Armed Away (since 2.2.0)", ("20 12:00", "slot_end", "Weg", "armed_away") in short(up), True)
    up, _ = await run(True, {"slots_on": False})
    check("slots off: nothing", up, [])
    up, _ = await run(True, {"outside": "none"})
    check("change nothing: end has no state", [e["state"] for e in up if e["kind"] == "slot_end"], [None])
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
