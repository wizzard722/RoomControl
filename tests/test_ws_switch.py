import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol as RC
from roomcontrol.const import DOMAIN
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
class Conn:
    def __init__(s): s.out=[]
    def send_result(s, i, r=None): s.out.append(("ok", r))
    def send_error(s, i, c, m): s.out.append(("err", c))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls=[]
    for svc in ("turn_on","turn_off"):
        async def h(c, s=svc): calls.append((s, c.data["entity_id"])); [hass.states.async_set(x, "on" if s=="turn_on" else "off") for x in c.data["entity_id"]]
        hass.services.async_register("switch", svc, h)
    hass.states.async_set("switch.tv","off"); hass.states.async_set("switch.koelkast","on"); hass.states.async_set("switch.vreemd","off")
    hass.data[DOMAIN] = {"rooms":[{"area_id":"k","switches":[{"entity_id":"switch.tv"},{"entity_id":"switch.koelkast","may_off":False}]}],"settings":{}}
    handler = RC.ws_call_service.__wrapped__ if hasattr(RC.ws_call_service,"__wrapped__") else RC.ws_call_service
    async def call(domain, service, eid):
        c=Conn(); m={"id":1,"type":"roomcontrol/call_service","domain":domain,"service":service,"entity_id":eid,"data":{}}
        r = handler(hass, c, m)
        if asyncio.iscoroutine(r): await r
        await hass.async_block_till_done(); return c.out[-1] if c.out else None
    check("tv off → on", (await call("switch","turn_on","switch.tv"))[0], "ok")
    check("tv state", hass.states.get("switch.tv").state, "on")
    check("tv on → off", (await call("switch","turn_off","switch.tv"))[0], "ok")
    check("fridge may never go off", await call("switch","turn_off","switch.koelkast"), ("err","not_allowed"))
    check("fridge stays on", hass.states.get("switch.koelkast").state, "on")
    check("switch not in a room refused", await call("switch","turn_on","switch.vreemd"), ("err","not_found"))
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
