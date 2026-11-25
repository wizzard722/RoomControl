import asyncio, sys, tempfile, types
from unittest.mock import patch
from datetime import datetime
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
import roomcontrol.light as L

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got} (want {want})")

async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    room = {"area_id": "slk", "covers": ["cover.slk"], "covers_follow": True}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    e = RoomControlLight.__new__(RoomControlLight); e.hass, e._area_id = hass, "slk"

    def at(hh, mm, sun, elev, rising):
        hass.states.async_set("sun.sun", sun, {"elevation": elev, "rising": rising})
        with patch.object(L.dt_util, "now", return_value=datetime(2026, 11, 18, hh, mm)):
            return e._covers_wanted_open()

    # no schedule, no "open at": never opens automatically (as before)
    check("legacy 10:00 light", at(10, 0, "above_horizon", 20, True), None)
    check("legacy 22:00 dark", at(22, 0, "below_horizon", -20, False), False)
    # open at sunrise (Sun integration)
    room["covers_open_at"] = "light"
    check("light 06:00 before sunrise", at(6, 0, "below_horizon", -5, True), False)
    check("light 08:10 just after sunrise", at(8, 10, "above_horizon", 1, True), True)
    check("light 15:00 day", at(15, 0, "above_horizon", 15, False), True)
    check("light 17:30 evening dark", at(17, 30, "below_horizon", -3, False), False)
    # fixed time 07:00
    room["covers_open_at"], room["covers_open_time"] = "time", "07:00"
    check("time 06:59 dark", at(6, 59, "below_horizon", -8, True), False)
    check("time 07:00 still dark: open", at(7, 0, "below_horizon", -6, True), True)
    check("time 23:00 night: closed", at(23, 0, "below_horizon", -30, False), False)
    room["covers_open_time"] = "09:30"
    check("time 09:00 sun up but before time", at(9, 0, "above_horizon", 8, True), False)
    check("time 09:30 open", at(9, 30, "above_horizon", 10, True), True)
    # evening close at dusk still works
    room["covers_close_at"] = "dusk"
    check("close at dusk evening", at(16, 30, "above_horizon", 3, False), False)
    # fixed-time timer registration
    e._cancel_cover_time = None
    e._setup_cover_time()
    check("timer scheduled", e._cancel_cover_time is not None, True)
    e._cancel_cover_time()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
