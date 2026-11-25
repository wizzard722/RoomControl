import asyncio, os, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.predict as PR, roomcontrol.rooms as RM, roomcontrol.switch as SW
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class FakeLight:
    def __init__(self): self._members = ["light.w"]; self._last_motion_at = dt_util.utcnow() - timedelta(hours=6); self._session_start = None
    def _own_motion(self): return False
    def _media_active(self): return False
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.time_zone = "Europe/Amsterdam"; dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
    await hass.async_start()
    slot = {"days": [0, 1, 2, 3, 4, 5, 6], "start": {"type": "time", "time": "18:00"}, "end": {"type": "time", "time": "23:00"}}
    room = {"area_id": "woonkamer", "groups": [{"id": "g", "own_times": True, "slots": [slot]}, {"id": "h", "slots": [{**slot, "start": {"type": "time", "time": "06:00"}, "end": {"type": "time", "time": "07:00"}}]}]}
    hass.data[DOMAIN] = {"rooms": [room], "entities": {"woonkamer": FakeLight()}, "settings": {}}
    hass.states.async_set("light.w", "off")
    patch.object(RM, "managed_areas", lambda h: {"woonkamer"}).start()
    patch.object(SW, "_sun_phase", lambda h: ("light", False)).start()
    p = PR.Predictor(hass)
    st = p.status("woonkamer")
    tl, sl = st["timeline"], st["slots"]
    check("prior on (new model, has slots)", st["prior"], True)
    check("slots strip: 18:00–23:00 only (bundle without own_times ignored)", (sl[18 * 4], sl[22 * 4 + 3], sl[23 * 4], sl[6 * 4], sl[12 * 4]), (True, True, False, False, False))
    check("new model: in a slot ~70 %, outside ~15 %", (tl[19 * 4], tl[12 * 4]), (70, 15))
    # inside a slot now → the feature is there
    at = dt_util.as_utc(dt_util.start_of_local_day() + timedelta(hours=19))
    now_f, day_f = p.features("woonkamer", at, {"motion": False, "lamps": False, "media": False, "since": 400})
    check("slot_on feature at 19:00", ("slot_on" in now_f, "slot_on" in day_f), (True, True))
    at = dt_util.as_utc(dt_util.start_of_local_day() + timedelta(hours=12))
    now_f, _d = p.features("woonkamer", at, {"motion": False, "lamps": False, "media": False, "since": 400})
    check("no slot_on at 12:00", "slot_on" in now_f, False)
    # after enough learning the prior no longer counts
    r = p.rooms.setdefault("woonkamer", PR.RoomPredictor()); r.now.n = PR.PRIOR_SAMPLES
    check("blend: learned enough → model only", round(p._blend(r, 0.4, True, True), 2), 0.4)
    r.now.n = PR.PRIOR_SAMPLES // 2
    check("blend: half way → mix", round(p._blend(r, 0.4, True, True), 2), round(0.5 * 0.4 + 0.5 * 0.7, 2))
    check("no slots → model only", p._blend(r, 0.4, True, False), 0.4)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
