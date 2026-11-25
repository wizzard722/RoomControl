import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.offpay as O
from roomcontrol.device_learning import Learner
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    key="badkamer|switch:switch.boiler"
    room={"area_id":"badkamer","power":{"switch:switch.boiler":{"ready_by":"06:30"}}}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{"energy":{"price_kwh":0.25}}}
    L=Learner({"run_w":2000}); L.data["cycles"]=[{"start":(dt_util.utcnow()-timedelta(hours=i*3)).isoformat(),"min":12,"kwh":0.2} for i in range(60)][::-1]
    learning=types.SimpleNamespace(learners={key:L}, sensors={key:"sensor.boiler_w"}, names={key:"Boiler"})
    op=O.OffPay(hass, learning)
    today=dt_util.as_local(dt_util.utcnow()).replace(hour=0,minute=0,second=0,microsecond=0)
    def price(h): return 0.38 if h in (6,7) else 0.15 if 2<=h<=4 else 0.24
    periods=[]
    for d in range(1,21):
        day=today-timedelta(days=d)
        for h in range(24):
            t=day+timedelta(hours=h); hk=O.hour_key(t)
            op.prices[hk]=price(h)
            off_night = d<=10   # last 10 nights switched off 00:30–06:00
            if off_night and h<6: kwh=0.0 if h>0 else 0.04
            elif off_night and h==6: kwh=0.08+0.45
            else: kwh=0.08
            L.data["hours"][hk]=kwh
        if d<=10: periods.append({"off":(day+timedelta(minutes=30)).isoformat(),"on":(day+timedelta(hours=6)).isoformat(),"why":"night"})
    op.periods={"switch.boiler":sorted(periods,key=lambda p:p["off"])}
    a=op.analysis(key)
    print("kind:",a["kind"],a["guessed"]); r=a["reasons"][0]; print("reason:",r)
    check("kind guessed warm", (a["kind"],a["guessed"]), ("warm",True))
    check("10 nights, fair+ confidence", (r["why"], r["n"], r["confidence"]), ("night",10,"good"))
    check("saved ≈ 5 h × 0.08", round(r["saved_kwh"],2), 0.4)
    check("catching up ≈ 0.45 kWh", round(r["back_kwh"],2), 0.45)
    check("net negative (more expensive)", r["net"] < 0, True)
    print("advice:", a["advice"])
    check("advice: back on in cheap block", a["advice"]["on"][:2] in ("02","03","04"), True)
    check("advice pays", a["advice"]["net_day"] > r["net"], True)
    # trial
    op.switches=lambda: {key:"switch.boiler"}
    op.start_trial(key); check("trial status", (op._trial_status(key)["night"], op._trial_status(key)["on"]), (1,"06:30"))
    op.stop_trial(key); check("trial stopped", op._trial_status(key), None)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
