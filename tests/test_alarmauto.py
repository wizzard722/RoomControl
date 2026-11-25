import asyncio, sys, tempfile, types
from datetime import datetime
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
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    P = "alarm_control_panel.alarmo"
    def reg(domain, svc, effect=None):
        async def h(c):
            calls.append((domain, svc, dict(c.data)))
            if effect: effect(c)
        hass.services.async_register(domain, svc, h)
    for svc, st in A.SERVICE_FOR.items(): reg("alarm_control_panel", st, (lambda c, st=svc: hass.states.async_set(P, st)))
    for d, s in [("lock","lock"),("notify","mobile_app_x"),("tts","speak"),("media_player","volume_set"),("media_player","play_media"),("media_player","media_stop"),("select","select_option"),("light","turn_on"),("light","turn_off"),("text","set_value")]: reg(d, s)
    hass.states.async_set(P, "disarmed"); hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    hass.states.async_set("person.paul", "home", {"friendly_name": "Paul"}); hass.states.async_set("person.sarah", "home", {"friendly_name": "Sarah"})
    hass.states.async_set("sensor.afstand", "3200", {"unit_of_measurement": "m"})
    hass.states.async_set("tts.piper", "unknown")
    alarm_cfg = {"slots": [{"name": "Nacht", "days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "23:30"}, "end": {"type": "time", "time": "06:30"}, "state": "armed_home"}],
                 "persons": ["person.paul", "person.sarah"], "away_delay": 0.001, "distance_sensor": "sensor.afstand", "distance_km": 100,
                 "locks": ["lock.slot"], "notify": "notify.mobile_app_x", "home_minutes": 10,
                 "screen": {"text": "text.nspanel"},
                 "lamps": {"lights": ["light.wled_voordeur"], "selects": ["select.wled_voordeur_preset"], "presets": {"armed_home": "2.Armed Home", "triggered": "Alert"}, "motion": ["binary_sensor.pir"], "off_minutes": 10},
                 "states": {"armed_home": {"screen_title": "Alarm Systeem", "screen_text": "Armed Home is ingeschakeld.", "screen_clear": 60},
                            "triggered": {"speak": "Het ALARM SYSTEEM is afgegaan", "players": ["media_player.cast"], "volume": 40, "volume_after": 20, "repeat": 5, "siren": "http://x/alarm.mp3", "siren_players": ["media_player.huiskamer"]}}}
    hass.data[DOMAIN] = {"settings": {"alarm_entity": P, "announce_tts": "tts.piper", "alarm": alarm_cfg}, "rooms": []}
    a = A.AlarmAutomation(hass); hass.data[DOMAIN]["alarm"] = a
    t = {"now": datetime(2026, 11, 19, 22, 0)}
    with patch.object(A.dt_util, "now", side_effect=lambda: t["now"]), patch("roomcontrol.announce.announce_tts", return_value="tts.piper"), patch.object(A, "announce_tts", return_value="tts.piper"):
        a.start(); await hass.async_block_till_done()
        check("22:00 startup: nothing set", [c for c in calls if c[0]=="alarm_control_panel"], [])
        t["now"] = datetime(2026, 11, 19, 23, 31); a._tick(); await hass.async_block_till_done()
        check("23:31 night slot starts: Armed Home", hass.states.get(P).state, "armed_home")
        calls.clear()
        hass.states.async_set("person.paul", "not_home", {"friendly_name": "Paul"}); await hass.async_block_till_done()
        check("Paul leaves at night: disarm? no (was home, armed stays)", hass.states.get(P).state, "armed_home")
        hass.states.async_set("person.paul", "home", {"friendly_name": "Paul"}); await hass.async_block_till_done()
        check("Paul comes home in slot: disarmed", hass.states.get(P).state, "disarmed")
        check("no screen or lamp calls any more", [c for c in calls if c[0] in ("text", "select", "light")], [])
        check("message", [c[2]["message"] for c in calls if c[0]=="notify"], ["Paul komt thuis. Alarm is uitgeschakeld voor 10 minuten."])
        check("re-arm pending", a._rearm_timer is not None, True)
        a._rearm_timer(); a._rearm_timer = None
        t["now"] = datetime(2026, 11, 20, 6, 31); a._tick(); await hass.async_block_till_done()
        # slot ended while disarmed: nothing to do
        calls.clear()
        # everyone away, close by
        t["now"] = datetime(2026, 11, 20, 9, 0); a._tick()
        hass.states.async_set("person.paul", "not_home", {"friendly_name": "Paul"}); hass.states.async_set("person.sarah", "not_home"); await hass.async_block_till_done(); await asyncio.sleep(0.3); await hass.async_block_till_done()
        check("everyone away 3.2 km: lock + Armed Home", ([c[1] for c in calls if c[0]=="lock"], hass.states.get(P).state), (["lock"], "armed_away"))
        hass.states.async_set("sensor.afstand", "150000", {"unit_of_measurement": "m"}); await hass.async_block_till_done()
        check("150 km away: Armed Vacation", hass.states.get(P).state, "armed_vacation")
        hass.states.async_set("sensor.afstand", "40", {"unit_of_measurement": "km"}); await hass.async_block_till_done()
        check("back within 100 km: Armed Away", hass.states.get(P).state, "armed_away")
        calls.clear()
        hass.states.async_set(P, "triggered"); await hass.async_block_till_done(); await asyncio.sleep(0.2)
        check("triggered: volume 40, speak, no siren (removed)", [(c[0], c[1]) for c in calls if c[0] in ("media_player","tts")][:2] + [any(c[1]=="play_media" for c in calls)], [("media_player","volume_set"),("tts","speak"),False])
        hass.states.async_set(P, "disarmed"); await hass.async_block_till_done(); await asyncio.sleep(5.5); await hass.async_block_till_done()
        check("disarmed: loop stops, volume back to 20", [c[2].get("volume_level") for c in calls if c[1]=="volume_set"][-1], 0.2)
        n = len([c for c in calls if c[0]=="tts"]); await asyncio.sleep(0.2)
        check("no more speaking", len([c for c in calls if c[0]=="tts"]), n)
        st = a.status(); check("status", (st["state"], st["distance_km"], st["away_target"]), ("disarmed", 40.0, "armed_away"))
        a.stop()
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
