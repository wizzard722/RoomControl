import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def run(states, extra=None, skip_on=False):
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    for dom, svc in (("tts","speak"),("notify","mobile_app_paul"),("media_player","volume_set")):
        async def h(c, d=dom, s=svc): calls.append((d, s, dict(c.data)))
        hass.services.async_register(dom, svc, h)
    notes = []
    orig = A.persistent_notification.async_create
    A.persistent_notification.async_create = lambda h, msg, title=None, notification_id=None: notes.append((title, msg))
    hass.states.async_set("tts.google", "idle"); hass.states.async_set("person.paul", "home", {"friendly_name": "Paul"}); hass.states.async_set("person.sarah", "home", {"friendly_name": "Sarah"})
    hass.states.async_set("input_boolean.stil", "on" if skip_on else "off")
    hass.data[DOMAIN] = {"rooms": [{"area_id": "wk", "media_players": ["media_player.wk"]}],
        "settings": {"alarm_entity": "alarm_control_panel.x", "persons": ["person.paul", "person.sarah"], "announce_tts": "tts.google",
                     "person_notify": {"person.paul": "notify.mobile_app_paul", "person.sarah": "none"},
                     "alarm": {"notify_skip": "input_boolean.stil", "states": states, **(extra or {})}}}
    with __import__("unittest.mock").mock.patch.object(A, "managed_areas", lambda h: {"wk"}), __import__("unittest.mock").mock.patch.object(A, "announce_tts", lambda h: "tts.google"):
        a = A.AlarmAutomation(hass)
        r = await a.test_state("armed_away"); await hass.async_block_till_done()
    A.persistent_notification.async_create = orig
    await hass.async_stop()
    return r, [(c[0], c[1]) for c in calls], notes
async def main():
    r, calls, notes = await run({})
    print(r, calls, notes)
    check("armed_away default: message only, no speech", (("tts","speak") in calls, ("notify","mobile_app_paul") in calls, len(notes)), (False, True, 1))
    check("result", (r.get("speak"), r["notify"]["services"], r["notify"]["ha"], r["notify"]["no_device"]), (None, ["paul"], True, ["Sarah"]))
    check("test title", notes[0][0], "Alarm Systeem (test)")
    r, calls, notes = await run({"armed_away": {"text": "Hoi", "speak_on": True, "notify_on": False}})
    check("speech only", (("tts","speak") in calls, ("notify","mobile_app_paul") in calls, len(notes), r["speak"]), (True, False, 0, {"players": 1, "tts": True}))
    r, calls, notes = await run({"armed_away": {"text": "Hoi", "speak_on": True, "notify_on": True, "notify_ha": False}}, skip_on=True)
    check("skip on + HA off: nothing to persons", (("notify","mobile_app_paul") in calls, len(notes), r["notify"]["skipped"]), (False, 0, True))
    r, calls, notes = await run({"armed_away": {"text": "Hoi", "speak_on": False, "notify_on": False}})
    check("both off: nothing", (calls, notes, "speak" in r, "notify" in r), ([], [], False, False))
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
