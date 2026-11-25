import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.clocks as C
ok=True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    hass.data["roomcontrol"]={}
    work={"id":"w","time":"06:30"}; both={"id":"b","time":"08:30","vacation":["home","away"]}; all3={"id":"a","vacation":["away","normal","home"]}
    for vac, want in ((None,(None,"normal","normal")),("home",("home",None,None)),("away",("away",None,None)),(True,("home",None,None))):
        hass.data["roomcontrol"]["vacation"]=vac
        check(f"vacation={vac}: skip work/vacation/all", (C.clock_skip(hass,work), C.clock_skip(hass,both), C.clock_skip(hass,all3)), (want[0], want[1], None))
    check("default modes", C.clock_modes(work), ["normal"]); check("ordered", C.clock_modes(all3), ["normal","home","away"]); check("empty never", C.clock_modes({"vacation":[]}), [])
    # ring: skipped clock logs blocked and does nothing
    hass.data["roomcontrol"]["vacation"]="home"
    logged=[]
    class L: 
        def _dbg(self,*a,**k): logged.append((a,k))
    room={"area_id":"slk","alarm_clocks":[{**work,"enabled":True,"bundles":[]}],"groups":[]}
    hass.data["roomcontrol"].update({"rooms":[room],"entities":{"slk":L()}})
    m=C.AlarmClocks(hass) if hasattr(C,"AlarmClocks") else None
    if m is None:
        cls=[v for k,v in vars(C).items() if isinstance(v,type) and hasattr(v,"_ring")][0]; m=cls(hass)
    m.start(); await m._ring("slk:w",0)
    st=m.states["slk:w"]
    check("skipped: not ringing, logged why", (st.ringing if hasattr(st,"ringing") else None, logged[0][1].get("why") if logged else None), (False,"clock_home"))
    [s.cancel() for s in m.states.values()]; await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
