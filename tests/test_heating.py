"""Heating (RoomMind): rules switch the schedule selector and put it back; gas equivalent; heater kWh per day."""
import asyncio, sys, tempfile, types
from datetime import timedelta, datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.heating as HT
import roomcontrol.energy_meter as EM

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); dt_util.set_default_time_zone(dt_util.get_time_zone("Europe/Amsterdam")); await hass.async_start()
    calls = []
    async def set_value(call): calls.append((call.data["entity_id"], call.data["value"])); hass.states.async_set(call.data["entity_id"], str(float(call.data["value"])), {"min": 1, "max": 3})
    hass.services.async_register("input_number", "set_value", set_value)
    S = hass.states.async_set
    S("input_number.schema_huis", "1.0", {"min": 1, "max": 3}); S("input_number.schema_woon", "2.0", {"min": 1, "max": 3})
    S("alarm_control_panel.a", "disarmed"); S("person.p", "home")
    S("schedule.woon_normaal", "on", {"friendly_name": "Woon normaal"}); S("schedule.woon_thuis", "off", {"friendly_name": "Woon thuiswerk"})
    S("climate.roommind_woon", "heat", {"current_temperature": 19.4, "temperature": 21, "hvac_action": "heating"})
    S("switch.ir", "on", {"friendly_name": "Infrarood"})
    rooms = [{"area_id": "woon", "heating": {"scope": "room", "selector": "input_number.schema_woon", "schedules": ["schedule.woon_normaal", "schedule.woon_thuis"],
                                             "rules": {"armed_away": 3}}, "switches": [{"entity_id": "switch.ir", "kind": "heater"}]},
             {"area_id": "keuken", "heating": {"scope": "house", "climate": "climate.roommind_woon"}}]
    hass.data[DOMAIN] = {"rooms": rooms, "settings": {"alarm_entity": "alarm_control_panel.a", "persons": ["person.p"],
                         "heating": {"selector": "input_number.schema_huis", "names": {"1": "Normaal", "3": "Vakantie"},
                                     "rules": {"armed_away": 3, "nobody": 3}, "nobody_h": 2, "gas_price": 1.35}}}
    h = HT.Heating(hass); await h.async_load()
    h._tick(); await hass.async_block_till_done()
    check("nothing applies: no change", calls, [])
    S("alarm_control_panel.a", "armed_away"); h._tick(); await hass.async_block_till_done()
    check("armed away: both selectors to 3", sorted(calls), [("input_number.schema_huis", 3), ("input_number.schema_woon", 3)])
    check("held keeps the old values", (h.held["input_number.schema_huis"]["prev"], h.held["input_number.schema_woon"]["prev"]), (1, 2))
    calls.clear(); S("alarm_control_panel.a", "disarmed"); h._tick(); await hass.async_block_till_done()
    check("disarmed: back to 1 and 2", sorted(calls), [("input_number.schema_huis", 1), ("input_number.schema_woon", 2)])
    # someone changes it meanwhile: not put back
    calls.clear(); S("alarm_control_panel.a", "armed_away"); h._tick(); await hass.async_block_till_done()
    S("input_number.schema_woon", "1.0", {"min": 1, "max": 3}); calls.clear()
    S("alarm_control_panel.a", "disarmed"); h._tick(); await hass.async_block_till_done()
    check("changed by hand: room not put back, house is", calls, [("input_number.schema_huis", 1)])
    # nobody home for 2 h (house rule only)
    calls.clear(); S("person.p", "not_home"); t = dt_util.utcnow()
    h._tick(); await hass.async_block_till_done()
    check("just left: nothing yet", calls, [])
    with patch.object(HT.dt_util, "utcnow", return_value=t + timedelta(hours=2, minutes=1)):
        h._tick(); await hass.async_block_till_done()
    check("2 h nobody home: house to 3", calls, [("input_number.schema_huis", 3)])
    # gas equivalent
    g = HT.gas_equivalent(hass, 3.2, 0.80)
    check("3.2 kWh ≈ 0.364 m³, € 0.49", (g["m3"], g["eur_gas"]), (0.364, 0.49))
    g = HT.gas_equivalent(hass, 3.2, 0.80, "heatpump")
    check("heat pump COP 3.5: 11.2 kWh heat", (g["heat"], round(g["m3"], 2)), (11.2, 1.27))
    # schedule names: room helper first, else general name
    check("names", (HT.schedule_name(hass, "woon", 2), HT.schedule_name(hass, "keuken", 3)), ("Woon thuiswerk", "3 · Vakantie"))
    # heater kWh per day in the meter
    m = EM.EnergyMeter(hass); hass.data[DOMAIN]["meter"] = m
    hass.data[DOMAIN]["settings"]["energy"] = {"price_kwh": 0.25, "market_source": "fixed"}
    st = {"configured": True, "phases": {"L1": 800}, "phase_detail": {"L1": {"consumed": 800, "produced": 0}},
          "rooms": {"woon": {"phase": "L1", "watts": 600, "parts": [{"key": "switch:switch.ir", "kind": "switch", "name": "Infrarood", "watts": 600}]}}, "car": {}}
    t0 = dt_util.utcnow().replace(microsecond=0) - timedelta(hours=1)
    t0 = dt_util.as_utc(dt_util.as_local(t0).replace(hour=10, minute=0, second=0))
    with patch.object(EM.dt_util, "utcnow", return_value=t0 + timedelta(hours=1)):
        m.add(st, t0)
        for i in range(1, 121):
            m.add(st, t0 + timedelta(seconds=30 * i))
        tot = m.heat_totals("woon")
    check("heater 0.6 kWh today, € 0.15", (round(tot["day"]["kwh"], 2), round(tot["day"]["eur"], 2)), (0.6, 0.15))
    check("week and month include today", (round(tot["week"]["kwh"], 2), round(tot["month"]["kwh"], 2)), (0.6, 0.6))
    hass.data[DOMAIN]["energy"] = types.SimpleNamespace(last_status=st)
    with patch.object(EM.dt_util, "utcnow", return_value=t0 + timedelta(hours=1)):
        rs = HT.room_status(hass, "woon")
    check("room status", (rs["climate"], rs["value"], rs["heaters"][0]["watts"], rs["thermostat"]["current"], round(rs["gas"]["day"]["m3"], 3)),
          ("climate.roommind_woon", 1, 600, 19.4, 0.068))
    hs = HT.house_status(hass)
    check("house status: rooms and RoomMind found", ([r["area"] for r in hs["rooms"]], hs["roommind"]), (["woon", "keuken"], ["climate.roommind_woon"]))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
