import asyncio, sys, tempfile, types
from datetime import datetime, timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
import roomcontrol.light as L

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    now = dt_util.as_local(datetime(2026, 11, 18, 20, 0, tzinfo=dt_util.get_default_time_zone()))
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10, "next_rising": (now + timedelta(hours=11, minutes=50)).isoformat(), "next_setting": (now + timedelta(hours=21)).isoformat(), "next_dusk": (now + timedelta(hours=20, minutes=40)).isoformat()})
    hass.states.async_set("light.wk", "on", {"brightness": 200})
    a = ar.async_get(hass).async_create("Woonkamer")
    room = {"area_id": a.id, "lights": [{"entity_id": "light.wk"}], "covers": ["cover.wk"], "covers_follow": True,
            "covers_open_at": "time", "covers_open_time": "07:30",
            "groups": [{"id": "g1", "name": "Plafond", "lights": ["light.wk"], "own_times": True,
                        "slots": [{"days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "18:00"}, "end": {"type": "time", "time": "23:00"}, "dim_at": "22:30"}]}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {"all_dim_window": {"start": "23:00", "end": "07:00"}}, "entities": {}}
    with patch.object(L.dt_util, "now", return_value=now):
        e = RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_wk"; e._members = ["light.wk"]
        await e.async_added_to_hass()
        for ev in e.upcoming():
            print(dt_util.parse_datetime(ev["at"]).strftime("%a %H:%M"), ev["kind"], ev["names"])
    await hass.async_stop()
asyncio.run(main())
