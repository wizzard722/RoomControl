import sys, tempfile, types, asyncio
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    rooms = [{"area_id": "wk", "media_players": ["media_player.cast_huiskamer"]}, {"area_id": "kk", "media_players": ["media_player.keuken", "media_player.cast_huiskamer"]}, {"area_id": "hal", "media_players": []}]
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {"alarm": {}}}
    with patch.object(A, "managed_areas", return_value={"wk", "kk", "hal"}):
        a = A.AlarmAutomation(hass)
        check("no rooms chosen: every room's players", a._players({"speak": "x"}, "speak"), ["media_player.cast_huiskamer", "media_player.keuken"])
        check("one room chosen", a._players({"speak_rooms": ["kk"]}, "speak"), ["media_player.keuken", "media_player.cast_huiskamer"])
        check("older players list still used", a._players({"players": ["media_player.oud"]}, "speak"), ["media_player.oud"])
        check("rooms set win over older list", a._players({"players": ["media_player.oud"], "speak_rooms": ["wk"]}, "speak"), ["media_player.cast_huiskamer"])
        check("stop off: none", a._players({}, "stop"), [])
        check("stop on, no rooms: all", a._players({"stop": True}, "stop"), ["media_player.cast_huiskamer", "media_player.keuken"])
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
