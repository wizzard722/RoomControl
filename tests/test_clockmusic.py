import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from roomcontrol.const import DOMAIN, SIGNAL_CONFIG_UPDATED
from roomcontrol.clocks import ClockManager, ClockState
import roomcontrol.clocks as C

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for svc in ("play_media", "volume_set", "repeat_set", "media_stop"):
        async def rec(c, svc=svc):
            calls.append((svc, c.data.get("volume_level")))
            if svc == "play_media": hass.states.async_set("media_player.slk", "playing", {"supported_features": 0})
            if svc == "media_stop": hass.states.async_set("media_player.slk", "idle", {"supported_features": 0})
        hass.services.async_register("media_player", svc, rec)
    clock = {"id": "w1", "time": "07:00", "days": [0,1,2,3,4,5,6], "enabled": True, "once": True, "snooze": True, "snoozes": 3, "snooze_minutes": 5,
             "music": True, "media_player": "media_player.slk", "volume_start": 10, "volume_end": 40,
             "media": {"media_content_id": "x", "media_content_type": "music"}}
    room = {"area_id": "slk", "alarm_clocks": [clock]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}}
    async def save(h, rooms=None, **kw):
        h.data[DOMAIN]["rooms"] = rooms; async_dispatcher_send(h, SIGNAL_CONFIG_UPDATED)
    import roomcontrol
    roomcontrol._async_save = save
    hass.states.async_set("media_player.slk", "idle", {"supported_features": 0})
    m = ClockManager(hass); hass.data[DOMAIN]["clocks"] = m; m.start(); await hass.async_block_till_done()
    m._persons_home = lambda r, c: True
    key = "slk:w1"
    await m._ring(key, 0); await hass.async_block_till_done()
    check("once clock disabled itself", hass.data[DOMAIN]["rooms"][0]["alarm_clocks"][0]["enabled"], False)
    async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
    check("another config change: still ringing, music on", (m.states[key].ringing, m.states[key].music_on), (True, True))
    check("player still playing", hass.states.get("media_player.slk").state, "playing")
    # music stops by itself, then step 1: plays again
    hass.states.async_set("media_player.slk", "idle", {"supported_features": 0}); await hass.async_block_till_done()
    calls.clear(); await m._ring(key, 1); await hass.async_block_till_done()
    check("step 1 after the music stopped: plays again at step-1 volume", [c for c in calls if c[0] in ("volume_set", "play_media")], [("volume_set", 0.2), ("play_media", None)])
    calls.clear(); await m._ring(key, 2); await hass.async_block_till_done()
    check("step 2 while playing: only louder", calls, [("volume_set", 0.3)])
    # repeat: track ends → plays again
    m.find(key)[2]["music_repeat"] = True
    calls.clear(); hass.states.async_set("media_player.slk", "idle", {"supported_features": 0}); await hass.async_block_till_done(); await asyncio.sleep(0.1)
    check("repeat on: track over → plays again", [c[0] for c in calls if c[0] == "play_media"], ["play_media"])
    calls.clear(); hass.states.async_set("media_player.slk", "paused", {"supported_features": 0}); await hass.async_block_till_done()
    check("paused by a person: left alone", [c[0] for c in calls if c[0] == "play_media"], [])
    await m.stop(key); await hass.async_block_till_done()
    calls.clear(); hass.states.async_set("media_player.slk", "playing", {}); hass.states.async_set("media_player.slk", "idle", {}); await hass.async_block_till_done()
    check("after stop: no restart", calls, [])
    # a clock switched off while going off still stops
    m.find(key)[2]["once"] = False; m.find(key)[2]["enabled"] = True
    await m._ring(key, 0); await hass.async_block_till_done()
    room["alarm_clocks"][0]["enabled"] = False
    hass.data[DOMAIN]["rooms"] = [room]; async_dispatcher_send(hass, SIGNAL_CONFIG_UPDATED); await hass.async_block_till_done()
    check("switched off by hand while ringing: stops", m.states[key].ringing, False)
    m.stop_all = None
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
