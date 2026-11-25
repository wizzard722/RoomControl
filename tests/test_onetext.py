import sys, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from roomcontrol.alarm_auto import resolve_state, state_defaults
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
d = state_defaults("nl")
pick = lambda r: (r["text"], r["speak_on"], r["notify_on"], r["speak"], r["notify"])
check("pending default: spoken text, both on", pick(resolve_state(d["pending"], {})), ("Alarm Systeem is geactiveerd.", True, True, "Alarm Systeem is geactiveerd.", "Alarm Systeem is geactiveerd."))
check("arming default: speak only", pick(resolve_state(d["arming"], {}))[1:3], (True, False))
check("armed_away default: notify only", pick(resolve_state(d["armed_away"], {})), ("Armed Away is ingeschakeld.", False, True, "", "Armed Away is ingeschakeld."))
check("disarmed: default text, both off", pick(resolve_state(d["disarmed"], {})), ("Alarm Systeem is uitgeschakeld.", False, False, "", ""))
check("every state has a text", all(v["text"] for v in d.values()), True)
check("old own rooms only → new defaults", pick(resolve_state(d["triggered"], {"speak_rooms": ["wk"]}))[:3], ("Het Alarm Systeem is afgegaan.", True, True))
check("no legacy key leaks", "legacy" in resolve_state(d["pending"], {}), False)
check("old own speak emptied → message only, text = message", pick(resolve_state(d["pending"], {"speak": ""}))[:3], ("Het Alarm Systeem heeft gedetecteerd dat een sensor is afgegaan.", False, True))
check("old own texts → speak text wins", pick(resolve_state({}, {"speak": "A", "notify": "B"}))[:3], ("A", True, True))
check("new format", pick(resolve_state(d["pending"], {"text": "X", "speak_on": False, "notify_on": True})), ("X", False, True, "", "X"))
check("new: empty text sends nothing", pick(resolve_state(d["pending"], {"text": "", "speak_on": True, "notify_on": True}))[3:], ("", ""))
print("ALL PASS" if ok else "SOME FAILED")
