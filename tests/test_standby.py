import asyncio, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.room_switches as RS
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for d in ("switch", "remote", "media_player"):
        for s in ("turn_on", "turn_off"):
            async def h(c, s=s, d=d):
                ids = c.data["entity_id"]; ids = ids if isinstance(ids, list) else [ids]
                for e in ids: calls.append((s, e)); hass.states.async_set(e, "on" if s == "turn_on" else "off")
            hass.services.async_register(d, s, h)
    hass.data[DOMAIN] = {"rooms": [{"area_id": "huiskamer", "media_players": ["media_player.tv"],
        "switches": [{"entity_id": "remote.shield", "back_on": False}, {"entity_id": "switch.tv", "back_on": "standby"}, {"entity_id": "switch.versterker"}]}],
        "entities": {}, "settings": {}}
    patch.object(RS, "managed_areas", lambda h: {"huiskamer"}).start()
    patch.object(RS, "household_persons", lambda h: []).start()
    for e in ("switch.tv", "switch.versterker"): hass.states.async_set(e, "off")
    hass.states.async_set("remote.shield", "off"); hass.states.async_set("media_player.tv", "unavailable")
    r = RS.RoomSwitches(hass) if hasattr(RS, "RoomSwitches") else [v for v in vars(RS).values() if isinstance(v, type) and hasattr(v, "async_back")][0](hass)
    r.switched_off = ["switch.tv", "switch.versterker", "remote.shield"]
    await r.async_back("test"); await hass.async_block_till_done()
    check("plugs back on, remote not", sorted(c for c in calls if c[0] == "turn_on"), [("turn_on", "switch.tv"), ("turn_on", "switch.versterker")])
    calls.clear()
    # the TV wakes by itself and wakes the Shield (CEC)
    hass.states.async_set("media_player.tv", "on"); hass.states.async_set("remote.shield", "on"); await hass.async_block_till_done()
    check("woken TV and Shield go off again", sorted(calls), [("turn_off", "media_player.tv"), ("turn_off", "remote.shield")])
    calls.clear()
    # later (the user turns it on): left alone
    with patch.object(RS.dt_util, "utcnow", return_value=dt_util.utcnow() + timedelta(minutes=5)):
        hass.states.async_set("media_player.tv", "on"); await hass.async_block_till_done()
    check("not watched any more", calls, [])
    # plug without standby: nothing watched
    hass.data[DOMAIN]["rooms"][0]["switches"][1]["back_on"] = True
    hass.states.async_set("media_player.tv", "off"); r.switched_off = ["switch.tv"]; hass.states.async_set("switch.tv", "off")
    r._sb_until = {}; r._sb_retrack()
    await r.async_back("test"); await hass.async_block_till_done(); calls.clear()
    hass.states.async_set("media_player.tv", "on"); await hass.async_block_till_done()
    check("back_on Ja: TV left on", calls, [])
    r.stop(); await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
