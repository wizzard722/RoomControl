import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
import roomcontrol.room_switches as RS
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    calls=[]
    for d in ("switch","remote","media_player"):
        for sv in ("turn_on","turn_off"):
            async def h(c,d=d,sv=sv):
                calls.append((d,sv,sorted(c.data["entity_id"])))
                for e in c.data["entity_id"]: hass.states.async_set(e,"on" if sv=="turn_on" else "off")
            hass.services.async_register(d,sv,h)
    S=hass.states.async_set
    S("remote.shield","on"); S("switch.tv","on"); S("media_player.shield","playing"); S("media_player.sonos","idle"); S("media_player.kamer2","playing")
    RS.managed_areas=lambda h: {"woonkamer","slaapkamer"}
    hass.data["roomcontrol"]={"settings":{},"rooms":[
        {"area_id":"woonkamer","switches":[{"entity_id":"remote.shield"},{"entity_id":"switch.tv"}],"media_players":["media_player.shield","media_player.sonos"],"media_off_away":True},
        {"area_id":"slaapkamer","media_players":["media_player.kamer2"]}]}
    check("remote accepted as a room switch", [s["entity_id"] for s in RS.room_switches(hass.data["roomcontrol"]["rooms"][0])], ["remote.shield","switch.tv"])
    rs=RS.RoomSwitches(hass); await rs.async_load()
    await rs.async_away("nobody home"); await hass.async_block_till_done()
    check("media off in woonkamer only (sonos idle too)", sorted(c for c in calls if c[0]=="media_player"), [("media_player","turn_off",["media_player.shield","media_player.sonos"])])
    check("shield via remote, tv via switch", sorted(c for c in calls if c[0]!="media_player"), [("remote","turn_off",["remote.shield"]),("switch","turn_off",["switch.tv"])])
    check("slaapkamer player (no option) still playing", hass.states.get("media_player.kamer2").state, "playing")
    calls.clear(); await rs.async_back("someone home"); await hass.async_block_till_done()
    check("back on: remote + switch, media not", sorted(calls), [("remote","turn_on",["remote.shield"]),("switch","turn_on",["switch.tv"])])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
