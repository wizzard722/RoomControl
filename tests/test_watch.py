import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import roomcontrol.device_watch as W
import roomcontrol.room_switches as RS
from roomcontrol.device_learning import Learner
ok=True
def check(l,g,w):
    global ok; ok&=g==w; print(("PASS " if g==w else "FAIL ")+f"{l}: {g}"+("" if g==w else f" (want {w})"))
async def main():
    hass=HomeAssistant(tempfile.mkdtemp()); hass.config.language="nl"; await hass.async_start(); S=hass.states.async_set
    sent=[]
    W.persistent_notification=types.SimpleNamespace(async_create=lambda h,m,title=None,notification_id=None: sent.append(m))
    notified=[]
    async def nt(c): notified.append(c.data["message"])
    hass.services.async_register("notify","mobile_app_p",nt)
    W.person_notify_service=lambda h,p: "notify.mobile_app_p"
    room={"area_id":"keuken","power":{"switch:switch.vaat":{"programs":{"p1":"Eco"},"watch":{"done":True,"forgot":True,"forgot_hours":1}},
                                     "meter:koel":{"watch":{"cool":True}}}}
    hass.data["roomcontrol"]={"rooms":[room],"settings":{"persons":["person.p"],"device_notify":{"phone":True},"energy":{"price_kwh":0.25}},"entities":{}}
    S("person.p","home"); S("sensor.koel","0",{"unit_of_measurement":"W"}); S("sensor.vaat","2000",{"unit_of_measurement":"W"})
    learning=types.SimpleNamespace(learners={"keuken|switch:switch.vaat":Learner({}),"keuken|meter:koel":Learner({})},
        sensors={"keuken|switch:switch.vaat":"sensor.vaat","keuken|meter:koel":"sensor.koel"},
        names={"keuken|switch:switch.vaat":"Vaatwasser","keuken|meter:koel":"Koelkast"})
    w=W.DeviceWatch(hass, learning)
    w.run_done("keuken|switch:switch.vaat", {"kwh":0.92,"prog":"p1","min":190})
    await hass.async_block_till_done()
    check("done message", sent[-1], "Vaatwasser is klaar (Eco · 0,92 kWh · € 0,23).")
    check("also to phone", notified[-1:], [sent[-1]])
    S("person.p","not_home"); n=len(sent); w.run_done("keuken|switch:switch.vaat", {"kwh":0.9,"prog":None,"min":100}); check("nobody home: no done", len(sent), n); S("person.p","home")
    # forgotten: run started 70 min ago
    lv=learning.learners["keuken|switch:switch.vaat"]; lv.run={"start":dt_util.utcnow().timestamp()-70*60,"kwh":0,"samples":[],"below":None}
    w._tick(); check("forgotten after 1 h", sent[-1], "Vaatwasser staat al 1:10 uur aan.")
    n=len(sent); w._tick(); check("forgotten once per run", len(sent), n)
    # cool: zero for 31 min
    lk=learning.learners["keuken|meter:koel"]; w._tick(); lk.data["zero_since"]=(dt_util.utcnow()-timedelta(minutes=31)).isoformat()
    w._tick(); check("fridge no power", sent[-1], "Koelkast verbruikt al 30 minuten niets. Staat hij nog aan?")
    # cool more: last week 1.6 kWh/day vs 1.0 before
    S("sensor.koel","60",{"unit_of_measurement":"W"}); lk.data.pop("week_checked",None)
    local=dt_util.as_local(dt_util.utcnow())
    lk.data["days"]={(local-timedelta(days=i)).strftime("%Y-%m-%d"):(1.6 if i<=7 else 1.0) for i in range(1,36)}
    w._tick(); check("fridge more than normal", sent[-1], "Koelkast verbruikte de afgelopen week 60% meer dan normaal (11,2 kWh).")
    # night switches
    P="alarm_control_panel.a"; S(P,"disarmed"); S("switch.tv","on")
    hass.data["roomcontrol"]["settings"]["alarm_entity"]=P
    room["switches"]=[{"entity_id":"switch.tv","off_on":["night"]}]
    RS.managed_areas=lambda h: {"keuken"}
    calls=[]
    async def h(c): calls.append((c.service,c.data["entity_id"])); [S(x,"on" if c.service=="turn_on" else "off") for x in c.data["entity_id"]]
    hass.services.async_register("switch","turn_on",h); hass.services.async_register("switch","turn_off",h)
    sw=RS.RoomSwitches(hass); sw._store.async_delay_save=lambda *a,**k: None; sw.start()
    S(P,"armed_home"); await hass.async_block_till_done(); check("night: tv off", calls[-1:], [("turn_off",["switch.tv"])])
    S(P,"disarmed"); await hass.async_block_till_done(); check("morning: tv on", calls[-1:], [("turn_on",["switch.tv"])])
    sw.stop(); await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
