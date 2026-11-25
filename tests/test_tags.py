import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.tags as T
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls=[]
    for d,svcs in {"light":["turn_on","turn_off"],"switch":["turn_on","turn_off"],"lock":["lock","unlock"],"cover":["open_cover","close_cover"]}.items():
        for sv in svcs:
            async def h(c,d=d,sv=sv): calls.append((d,sv,sorted(c.data["entity_id"])))
            hass.services.async_register(d,sv,h)
    S=hass.states.async_set
    S("light.bundel","off"); S("switch.tv","off"); S("lock.voordeur","locked"); S("cover.gordijn","closed")
    hass.data["roomcontrol"]={"settings":{"tags":[{"tag_id":"abc","action":"toggle","targets":["light.bundel","switch.tv","lock.voordeur","cover.gordijn"]},{"tag_id":"xyz","action":"off","targets":["lock.voordeur"]}]}}
    t=T.Tags(hass); t.start()
    hass.bus.async_fire("tag_scanned",{"tag_id":"abc","device_id":"phone"}); await hass.async_block_till_done()
    check("toggle all off → on/open/unlock", sorted(calls), [("cover","open_cover",["cover.gordijn"]),("light","turn_on",["light.bundel"]),("lock","unlock",["lock.voordeur"]),("switch","turn_on",["switch.tv"])])
    check("last scan", (t.last["tag_id"], t.last["known"], t.last.get("turn")), ("abc", True, "on"))
    calls.clear(); S("light.bundel","on")
    hass.bus.async_fire("tag_scanned",{"tag_id":"abc"}); await hass.async_block_till_done()
    check("toggle with one on → all off/close/lock", sorted(calls), [("cover","close_cover",["cover.gordijn"]),("light","turn_off",["light.bundel"]),("lock","lock",["lock.voordeur"]),("switch","turn_off",["switch.tv"])])
    calls.clear(); hass.bus.async_fire("tag_scanned",{"tag_id":"xyz"}); await hass.async_block_till_done()
    check("off action → lock", calls, [("lock","lock",["lock.voordeur"])])
    calls.clear(); hass.bus.async_fire("tag_scanned",{"tag_id":"unknown"}); await hass.async_block_till_done()
    check("unknown tag: nothing, remembered", (calls, t.last["known"]), ([], False))
    from homeassistant.core import Context
    S("person.paul","home",{"user_id":"u-paul","device_trackers":[]}); S("person.sarah","home",{"user_id":"u-sarah","device_trackers":[]})
    hass.data["roomcontrol"]["settings"]["tags"]=[{"tag_id":"p","action":"on","targets":["switch.tv"],"persons":["person.paul"]}]
    calls.clear(); hass.bus.async_fire("tag_scanned",{"tag_id":"p"},context=Context(user_id="u-sarah")); await hass.async_block_till_done()
    check("Sarah may not", (calls, t.last.get("refused"), t.last["person"]), ([], True, "person.sarah"))
    hass.bus.async_fire("tag_scanned",{"tag_id":"p"},context=Context(user_id="u-paul")); await hass.async_block_till_done()
    check("Paul may", calls, [("switch","turn_on",["switch.tv"])])
    calls.clear(); hass.bus.async_fire("tag_scanned",{"tag_id":"p","device_id":"reader"}); await hass.async_block_till_done()
    check("fixed reader (no person) refused", calls, [])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
