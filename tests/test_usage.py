import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.offpay as O
from roomcontrol.device_learning import Learner
from roomcontrol.usage import usage
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    room={"area_id":"keuken","power":{"switch:switch.espresso":{"kind":"warm"},"switch:switch.tv":{"kind":"standby"}}}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{"energy":{"price_kwh":0.25}}}
    E=Learner({"run_w":1200}); TV=Learner({})
    learning=types.SimpleNamespace(learners={"keuken|switch:switch.espresso":E,"keuken|switch:switch.tv":TV}, sensors={}, names={})
    op=O.OffPay(hass, learning)
    today=dt_util.as_local(dt_util.utcnow()).date()
    for i in range(1,29):
        d=today-timedelta(days=i); wd=d.weekday()
        qs=list(range(28,32))+list(range(72,76)) if wd<5 else list(range(36,40))
        E.data["use"][d.isoformat()]={"all":qs+[4,40,80],"big":qs}
        TV.data["use"][d.isoformat()]={"all":list(range(76,92)),"big":[]}
        for h in range(24):
            hk=f"{d.isoformat()}T{h:02d}"
            E.data["hours"][hk]=0.03; TV.data["hours"][hk]=0.012
    u=usage(op,"keuken|switch:switch.espresso")
    print("espresso groups:", u["groups"]); print("proposal:", [(p["days"],p["start"]["time"],p["end"]["time"]) for p in u["proposal"]], "per month", u["per_month"])
    check("weekdays windows with 30 min lead", u["groups"][0], {"days":[0,1,2,3,4],"windows":["06:30–08:00","17:30–19:00"]})
    check("weekend window", u["groups"][1], {"days":[5,6],"windows":["08:30–10:00"]})
    check("keep-warm pulses ignored (big only)", any("01:00" in w for g in u["groups"] for w in g["windows"]), False)
    t=usage(op,"keuken|switch:switch.tv")
    print("tv groups:", t["groups"], "proposal:", [(p["days"],p["start"]["time"],p["end"]["time"]) for p in t["proposal"]], "per month", t["per_month"])
    check("tv used 19:00–23:00 daily", t["groups"], [{"days":[0,1,2,3,4,5,6],"windows":["19:00–23:00"]}])
    check("tv off slot crosses midnight", [(p["start"]["time"],p["end"]["time"]) for p in t["proposal"]], [("23:00","19:00")])
    check("tv saves money", t["per_month"] > 0, True)
    E.data["use"]={today.isoformat():{"all":[1],"big":[1]}}; check("too little data", usage(op,"keuken|switch:switch.espresso")["enough"], False)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
