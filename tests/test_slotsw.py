import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.room_switches as RS
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); await hass.async_start(); S=hass.states.async_set
    now=dt_util.as_local(dt_util.now()); a=(now-timedelta(minutes=5)).strftime("%H:%M"); b=(now+timedelta(minutes=30)).strftime("%H:%M")
    slot={"days":[0,1,2,3,4,5,6],"start":{"type":"time","time":a},"end":{"type":"time","time":b}}
    room={"area_id":"bad","switches":[{"entity_id":"switch.boiler","off_on":["slot"],"slots":[slot]}]}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{}}
    RS.managed_areas=lambda h: {"bad"}
    S("switch.boiler","on"); calls=[]
    async def h(c): calls.append(c.service); [S(x,"on" if c.service=="turn_on" else "off") for x in c.data["entity_id"]]
    hass.services.async_register("switch","turn_on",h); hass.services.async_register("switch","turn_off",h)
    sw=RS.RoomSwitches(hass); sw._store.async_delay_save=lambda *a,**k: None
    sw._slot_tick(); await hass.async_block_till_done()
    check("slot running → off, reason kept", (calls, hass.data["roomcontrol"]["switch_why"].get("switch.boiler")), (["turn_off"],"slot"))
    slot["start"]["time"]=(now+timedelta(minutes=10)).strftime("%H:%M"); sw._slot_tick(); await hass.async_block_till_done()
    check("slot over → back on", calls, ["turn_off","turn_on"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
