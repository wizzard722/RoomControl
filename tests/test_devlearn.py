import sys, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from roomcontrol.device_learning import Learner, PROGRAM_MIN
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
L=Learner({"sensor":"sensor.x"})
t=1_700_000_000.0
def idle(minutes, w=1.2):
    global t
    for _ in range(minutes): L.feed(t, w); t+=60
def run(pattern):
    """pattern: list of (minutes, W)"""
    global t
    done=None
    for m,w in pattern:
        for _ in range(m):
            r=L.feed(t,w); done=done or r; t+=60
    for _ in range(12):
        r=L.feed(t,1.2); done=done or r; t+=60
    return done
eco=[(2,80),(15,2100),(100,60),(12,2050),(30,40),(30,8)]
snel=[(25,2100),(5,90),(20,2000),(10,30)]
idle(60)
check("standby learned", round(L.data["standby"],1), 1.2)
runs=[]
for i in range(4): runs.append(run(eco)); idle(300)
for i in range(3): runs.append(run(snel)); idle(300)
p=L.data["programs"]
check("two programs", len(p), 2)
counts=sorted((v["n"], round(v["min"]), round(v["kwh"],2)) for v in p.values())
print("programs:", counts)
check("eco recognised 4x, snel 3x", [c[0] for c in counts], [3,4])
check("all runs matched a program", all(r and r["prog"] for r in runs), True)
check("heat counted", sum(sum(r) for r in L.data["heat"]), 7)
check("days have energy", round(sum(L.data["days"].values()),2) > 5, True)
print("ALL PASS" if ok else "SOME FAILED")
