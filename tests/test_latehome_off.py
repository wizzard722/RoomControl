import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.switch import LateHomeSwitch
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {}}
    for start in ("not_home", "Werk"):
        hass.states.async_set("person.paul", start)
        sw = LateHomeSwitch("person.paul"); sw.hass = hass; sw.entity_id = "switch.later_thuis_paul"
        await sw.async_added_to_hass(); await sw.async_turn_on()
        print(start, "on:", sw.is_on)
        hass.states.async_set("person.paul", "home"); await hass.async_block_till_done(); await asyncio.sleep(0.05)
        print(start, "after home:", sw.is_on, hass.states.get("switch.later_thuis_paul").state)
    await hass.async_stop()
asyncio.run(main())
