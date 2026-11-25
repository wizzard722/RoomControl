import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
import roomcontrol.nspanel as N
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); hass.config.language="nl"; await hass.async_start()
    calls=[]
    for p in ("nspanel_woonkamer","nspanel_keuken"):
        for a in ("_notification_show","_notification_clear"):
            async def h(call, n=p+a): calls.append((n, dict(call.data)))
            hass.services.async_register("esphome", p+a, h)
    hass.services.async_register("esphome", "other_thing", lambda c: None)
    hass.data["roomcontrol"]={"settings":{"nspanel":{"on":True,"seconds":0.3,"sources":{"doorbell":False}}}}
    check("found", N.found_panels(hass), ["nspanel_keuken","nspanel_woonkamer"])
    N.nspanel_message(hass, "ev", "Audi laadt"); await hass.async_block_till_done()
    check("shown on both", sorted(c[0] for c in calls), ["nspanel_keuken_notification_show","nspanel_woonkamer_notification_show"])
    check("label", calls[0][1], {"label":"Auto laden","message":"Audi laadt"})
    await asyncio.sleep(0.6); await hass.async_block_till_done()
    check("cleared after seconds", sorted(c[0] for c in calls if c[0].endswith("clear")), ["nspanel_keuken_notification_clear","nspanel_woonkamer_notification_clear"])
    calls.clear(); N.nspanel_message(hass, "doorbell", "Er wordt aangebeld"); await hass.async_block_till_done()
    check("doorbell source off", calls, [])
    hass.data["roomcontrol"]["settings"]["nspanel"]["groups"]=[{"id":"g1","name":"Beneden","panels":["nspanel_keuken"]}]
    hass.data["roomcontrol"]["settings"]["nspanel"]["sources"]["alarm"]="g1"
    N.nspanel_message(hass, "alarm", "Armed Away"); await hass.async_block_till_done()
    check("alarm → group Beneden", [c[0] for c in calls], ["nspanel_keuken_notification_show"])
    calls.clear(); N.nspanel_message(hass, "alarm", "x", target="all"); await hass.async_block_till_done()
    check("own target all wins", len(calls), 2)
    calls.clear(); N.nspanel_message(hass, "alarm", "x", target="none"); await hass.async_block_till_done()
    check("own target none", calls, [])
    calls.clear(); N.nspanel_message(hass, "alarm", "x", target="gone"); await hass.async_block_till_done()
    check("removed group → nothing", calls, [])
    check("group by name", N.target_panels(hass, "Beneden"), ["nspanel_keuken"])
    # a new message restarts the timer
    calls.clear(); hass.data["roomcontrol"]["settings"]["nspanel"]["seconds"]=0.5
    N.nspanel_message(hass, "alarm", "1"); await hass.async_block_till_done(); await asyncio.sleep(0.3)
    N.nspanel_message(hass, "alarm", "2"); await hass.async_block_till_done(); await asyncio.sleep(0.35); await hass.async_block_till_done()
    check("no clear yet (timer restarted)", [c[0] for c in calls if c[0]=="nspanel_keuken_notification_clear"], [])
    await asyncio.sleep(0.3); await hass.async_block_till_done()
    check("cleared once", [c[0] for c in calls if c[0]=="nspanel_keuken_notification_clear"], ["nspanel_keuken_notification_clear"])
    hass.data["roomcontrol"]["settings"]["nspanel"]["on"]=False; calls.clear()
    N.nspanel_message(hass, "alarm", "x"); await hass.async_block_till_done(); check("off → nothing", calls, [])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
