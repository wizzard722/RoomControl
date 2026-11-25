import asyncio, sys, tempfile, types
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
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.language = "nl"; await hass.async_start()
    calls = []
    for d, s in [("tts","speak"),("media_player","volume_set"),("media_player","play_media"),("media_player","media_stop"),("notify","x")]:
        async def h(c, d=d, s=s): calls.append((d, s, dict(c.data)))
        hass.services.async_register(d, s, h)
    P = "alarm_control_panel.alarmo"
    hass.states.async_set(P, "disarmed")
    hass.data[DOMAIN] = {"settings": {"alarm_entity": P, "alarm": {"notify": "notify.x"}}, "rooms": [{"area_id": "wk", "media_players": ["media_player.wk"]}]}
    with patch.object(A, "managed_areas", return_value={"wk"}), patch.object(A, "announce_tts", return_value="tts.piper"):
        a = A.AlarmAutomation(hass)
        st = a.state_cfg("triggered")
        check("defaults for triggered (nl)", (st["speak"], st["volume"], st["volume_after"], st["repeat"], st["notify"]), ("Het Alarm Systeem is afgegaan.", 40, 20, 10, "Het Alarm Systeem is afgegaan."))
        hass.config.language = "en"
        check("defaults follow HA language", a.state_cfg("triggered")["speak"], "The alarm system has gone off.")
        hass.config.language = "nl"
        hass.data[DOMAIN]["settings"]["alarm"]["states"] = {"triggered": {"notify": "", "repeat": None, "siren": "/local/alarm.mp3"}}
        st = a.state_cfg("triggered")
        check("own empty values replace defaults", (st["notify"], st["repeat"], st["speak"]), ("", None, "Het Alarm Systeem is afgegaan."))
        a.start(); await hass.async_block_till_done()
        hass.states.async_set(P, "triggered"); await hass.async_block_till_done(); await asyncio.sleep(0.2)
        check("triggered: speak on the room's players, no siren, no message", ([c[1] for c in calls if c[0] in ("tts","media_player")][:2], "play_media" in [c[1] for c in calls], [c for c in calls if c[0]=="notify"]), (["volume_set","speak"], False, []))
        calls.clear()
        hass.states.async_set(P, "disarmed"); await hass.async_block_till_done(); await asyncio.sleep(0.2)
        check("disarmed after triggered: nothing to stop (no siren)", [c[2]["entity_id"] for c in calls if c[1]=="media_stop"], [])
        a.stop()
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
