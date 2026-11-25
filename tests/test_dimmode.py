import sys, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
import roomcontrol.switch as SW
class H: pass
slots=[{"days":[0],"start":{"type":"time","time":"23:00"},"end":{"type":"time","time":"07:00"}}]
for label,st,want_mode,want_slots in [
  ("alarm panel, nothing chosen → alarm", {"alarm_entity":"a","all_dim_slots":slots}, "alarm", 0),
  ("no alarm panel → slots", {"all_dim_slots":slots}, "slots", 1),
  ("older: follow switched off → slots", {"alarm_entity":"a","all_dim_follows_alarm":False,"all_dim_slots":slots}, "slots", 1),
  ("chosen slots", {"alarm_entity":"a","all_dim_mode":"slots","all_dim_slots":slots}, "slots", 1),
  ("chosen alarm but no panel → slots", {"all_dim_mode":"alarm","all_dim_slots":slots}, "slots", 1)]:
    h=H(); h.data={"roomcontrol":{"settings":st}}
    got=(SW.all_dim_mode(st), len(SW.all_dim_slots(h)))
    print(("PASS " if got==(want_mode,want_slots) else "FAIL ")+label, got)
