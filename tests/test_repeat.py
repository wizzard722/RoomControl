import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.clocks import ClockManager, ClockState

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for svc in ("play_media", "volume_set", "repeat_set", "media_stop"):
        async def rec(c, svc=svc): calls.append((svc, c.data.get("repeat")))
        hass.services.async_register("media_player", svc, rec)
    hass.data[DOMAIN] = {"rooms": [], "settings": {}}
    m = ClockManager(hass)
    clock = {"music": True, "media_player": "media_player.slk", "music_repeat": True,
             "media": {"media_content_id": "spotify:playlist:x", "media_content_type": "playlist"}}
    m._player = lambda k, c: c["media_player"]
    for label, feats, before in (("speaker can repeat", 262144, "one"), ("speaker can't repeat", 0, None)):
        calls.clear(); m.states["k"] = ClockState()
        hass.states.async_set("media_player.slk", "idle", {"supported_features": feats, **({"repeat": before} if before else {})})
        await m._music_start("k", clock, 0); await m._music_stop("k", clock)
        print(label, "→", calls)
    calls.clear(); m.states["k"] = ClockState(); clock["music_repeat"] = False
    hass.states.async_set("media_player.slk", "idle", {"supported_features": 262144, "repeat": "off"})
    await m._music_start("k", clock, 0); await m._music_stop("k", clock)
    print("repeat option off →", calls)
    await hass.async_stop()
asyncio.run(main())
