import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.control import rc_call, _matches, _wanted
from roomcontrol.clocks import ClockManager
from roomcontrol.rooms import cover_state

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    calls = []
    async def rec(c): calls.append((c.service, c.data.get("position"), tuple(c.data["entity_id"])))
    for s in ("open_cover", "close_cover", "set_cover_position", "stop_cover"):
        hass.services.async_register("cover", s, rec)
    hass.data[DOMAIN] = {"rooms": [{"area_id": "slk", "covers": ["cover.inv", "cover.norm"], "covers_inverted": ["cover.inv"]}]}
    # Alarm clock steps: 3 extra steps → 25, 50, 75, 100 %
    clock = {"snooze": True, "snoozes": 3, "covers_open": True}
    pcts = [ClockManager.cover_pct(clock, i) for i in range(4)]
    check("clock wants", pcts, [25, 50, 75, 100])
    for p in pcts:
        await rc_call(hass, "cover", "set_cover_position", {"entity_id": ["cover.inv"], "position": p})
    check("reversed curtain gets positions as-is", [c[1] for c in calls], [25, 50, 75, 100])
    calls.clear()
    await rc_call(hass, "cover", "open_cover", {"entity_id": ["cover.inv", "cover.norm"]})
    check("open: reversed gets close, normal gets open", sorted((c[0], c[2]) for c in calls),
          [("close_cover", ("cover.inv",)), ("open_cover", ("cover.norm",))])
    check("full control remembers what was meant", _wanted(hass)["cover.inv"]["cover"], "open")
    # State: curtain with a position reports correctly; without a position its state is swapped back.
    hass.states.async_set("cover.inv", "open", {"current_position": 100})
    check("state with position", cover_state(hass, hass.states.get("cover.inv")), "open")
    check("full control: open matches", _matches(hass, hass.states.get("cover.inv"), {"cover": "open"}), True)
    hass.states.async_set("cover.inv", "closed", {})
    check("state without position swapped", cover_state(hass, hass.states.get("cover.inv")), "open")
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
