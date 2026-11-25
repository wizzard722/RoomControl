import sys, types, tempfile, asyncio
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from roomcontrol.const import DOMAIN
from roomcontrol.person_notify import person_notify_service
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"person_notify": {"person.paul": "none", "person.sarah": "notify.mobile_app_sarah"}}}
    print("paul none ->", person_notify_service(hass, "person.paul"))
    print("sarah chosen ->", person_notify_service(hass, "person.sarah"))
    print("piet auto (nothing) ->", person_notify_service(hass, "person.piet"))
    await hass.async_stop()
asyncio.run(main())
