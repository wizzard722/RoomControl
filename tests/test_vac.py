import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar
import roomcontrol.switch as SW
from roomcontrol.slots import mode_slots
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    # Since 2.2.0: Vakantie (switch, follows the alarm's Armed Vacation) and Verlof (switch, by hand).
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await hass.async_start()
    hass.data["roomcontrol"] = {"settings": {}, "rooms": []}  # no alarm panel: plain switches
    vac = SW.VacationSwitch(); vac.hass = hass
    leave = SW.LeaveSwitch(); leave.hass = hass
    await leave.async_turn_on(); check("Verlof on → home", (hass.data["roomcontrol"]["vacation"], leave.is_on, vac.is_on), ("home", True, False))
    await vac.async_turn_on(); check("Vakantie on → away, Verlof off", (hass.data["roomcontrol"]["vacation"], leave.is_on, vac.is_on), ("away", False, True))
    try:
        await leave.async_turn_on(); refused = False
    except HomeAssistantError:
        refused = True
    check("Verlof can't while Vakantie is on", refused, True)
    await vac.async_turn_off(); check("Vakantie off → normal", (hass.data["roomcontrol"]["vacation"], vac.is_on), (False, False))
    check("attributes", vac.extra_state_attributes, {"roomcontrol_vacation": True, "vacation_kind": None})
    slots = [{"id": "n", "holiday": "normal"}, {"id": "v", "holiday": "vacation"}, {"id": "h", "holiday": "vacation_home"}, {"id": "a", "holiday": "vacation_away"}]
    ids = lambda m: [s["id"] for s in mode_slots(slots, m)]
    check("slots normal", ids(False), ["n"]); check("slots home (Verlof)", ids("home"), ["v", "h"]); check("slots away (Vakantie)", ids("away"), ["v", "a"]); check("legacy True = home", ids(True), ["v", "h"])
    check("only an away slot, on leave → normal ones", [s["id"] for s in mode_slots([{"id": "n"}, {"id": "a", "holiday": "vacation_away"}], "home")], ["n"])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
