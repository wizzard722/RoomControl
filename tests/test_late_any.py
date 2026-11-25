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
    hass.states.async_set("person.paul", "home")
    sw = LateHomeSwitch("person.paul"); sw.hass = hass; sw.entity_id = "switch.later_thuis_paul"
    await sw.async_added_to_hass(); await sw.async_turn_on(); print("on while home:", sw.is_on)
    hass.states.async_set("person.paul", "home", {"gps": 1}); await hass.async_block_till_done(); await asyncio.sleep(0.05)
    print("attr update while home keeps on:", sw.is_on)
    await sw.async_turn_off(); print("off:", sw.is_on); await sw.async_turn_on(); print("on again:", sw.is_on)
    hass.states.async_set("person.paul", "not_home"); await hass.async_block_till_done(); await asyncio.sleep(0.05); print("left:", sw.is_on)
    hass.states.async_set("person.paul", "home"); await hass.async_block_till_done(); await asyncio.sleep(0.05); print("came home:", sw.is_on)
    await hass.async_stop()
asyncio.run(main())
