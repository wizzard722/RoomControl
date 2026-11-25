import sys, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.util import dt as dt_util
dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam"))
import roomcontrol.device_learning as DL
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
L = DL.Learner({})
day = dt_util.start_of_local_day(dt_util.now().date() - timedelta(days=1))
t = (day + timedelta(hours=6)).timestamp()
# standby 2 W for an hour, readings every minute
for i in range(60): L.feed(t + i * 60, 2.0)
t += 3600  # 07:00
# a cup at 07:20: 1400 W for 45 s
for i in range(20): L.feed(t + i * 60, 2.0)
L.feed(t + 20 * 60, 1400.0); L.feed(t + 20 * 60 + 45, 2.0)
for i in range(21, 60): L.feed(t + i * 60, 2.0)
# a cup at 12:35
t2 = (day + timedelta(hours=12, minutes=35)).timestamp()
L.feed(t2 - 60, 2.0); L.feed(t2, 1400.0); L.feed(t2 + 40, 2.0); L.feed(t2 + 600, 2.0)
d = day.strftime("%Y-%m-%d")
e = sorted(L.data["use"].get(d, {}).get("e", []))
check("short cups counted as e use (07:15, 12:30 quarters)", e, [29, 50])
check("no runs (too short)", len(L.data["cycles"]), 0)
check("standby learned ~2 W", round(L.data["standby"]), 2)
check("qe kept small", len(L.data.get("qe", {})) <= 8, True)
print("ALL PASS" if ok else "SOME FAILED")
