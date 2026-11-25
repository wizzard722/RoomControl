import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.room_switches as RS, roomcontrol.offpay as O, roomcontrol
from roomcontrol.device_learning import Learner
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); await hass.async_start(); S=hass.states.async_set
    now=dt_util.as_local(dt_util.now())
    slot={"days":[0,1,2,3,4,5,6],"start":{"type":"time","time":(now-timedelta(minutes=5)).strftime("%H:%M")},"end":{"type":"time","time":(now+timedelta(hours=2)).strftime("%H:%M")}}
    room={"area_id":"woon","switches":[{"entity_id":"switch.tv","off_on":["slot"],"slots":[slot]}],"power":{"switch:switch.tv":{"auto_schedule":True,"kind":"standby"}}}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{}}
    RS.managed_areas=lambda h: {"woon"}
    L=Learner({}); L.last=(dt_util.utcnow().timestamp(), 80.0)
    learning=types.SimpleNamespace(learners={"woon|switch:switch.tv":L}, sensors={"woon|switch:switch.tv":"sensor.tv"}, names={"woon|switch:switch.tv":"Tv"})
    hass.data["roomcontrol"]["device_learning"]=learning
    S("switch.tv","on"); calls=[]
    async def h(c): calls.append(c.service); [S(x,"on" if c.service=="turn_on" else "off") for x in c.data["entity_id"]]
    hass.services.async_register("switch","turn_on",h); hass.services.async_register("switch","turn_off",h)
    sw=RS.RoomSwitches(hass); sw._store.async_delay_save=lambda *a,**k: None
    sw._slot_tick(); await hass.async_block_till_done(); check("slot → off", calls, ["turn_off"])
    S("switch.tv","on"); sw._slot_tick(); await hass.async_block_till_done(); check("on by hand, in use → stays on", calls, ["turn_off"])
    L.last=(dt_util.utcnow().timestamp(), 1.0); sw._slot_tick(); sw._idle_since["switch.tv"]-=31*60; sw._slot_tick(); await hass.async_block_till_done()
    check("idle 30 min → off again", calls, ["turn_off","turn_off"])
    # auto schedule writes the proposal
    saved=[]
    async def save(h, rooms=None, **k): saved.append(rooms)
    roomcontrol._async_save=save
    op=O.OffPay(hass, learning)
    import roomcontrol.usage as U
    U.usage=lambda o,k: {"enough":True,"proposal":[{"days":[0,1,2,3,4,5,6],"start":{"type":"time","time":"23:00"},"end":{"type":"time","time":"19:00"}}]}
    op._auto_schedules(dt_util.utcnow()); await hass.async_block_till_done()
    check("auto schedule saved", saved[0][0]["switches"][0]["slots"][0]["start"]["time"] if saved else None, "23:00")
    n=len(saved); op._auto_schedules(dt_util.utcnow()); await hass.async_block_till_done(); check("once a week", len(saved), n)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
