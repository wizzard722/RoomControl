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
    from homeassistant.helpers import entity_registry as er0; await er0.async_load(hass)
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
    # armed home, holiday, summer, and the order
    S("person.p", "home"); h._tick(); await hass.async_block_till_done()
    g = hass.data[DOMAIN]["settings"]["heating"]
    g["rules"] = {"armed_away": 3, "armed_home": 2, "holiday": 3, "summer": 4}
    g["holiday_calendar"] = "calendar.feestdagen"; S("calendar.feestdagen", "off"); S("sensor.season", "winter")
    S("input_number.schema_huis", "1.0", {"min": 1, "max": 4}); h.held.clear(); calls.clear()
    h._tick(); await hass.async_block_till_done()
    check("winter, no holiday: stays 1", calls, [])
    S("alarm_control_panel.a", "armed_home"); h._tick(); await hass.async_block_till_done()
    check("armed home: 2", calls[-1], ("input_number.schema_huis", 2))
    S("sensor.season", "summer"); h._tick(); await hass.async_block_till_done()
    check("armed home wins over summer", calls[-1], ("input_number.schema_huis", 2))
    S("alarm_control_panel.a", "disarmed"); h._tick(); await hass.async_block_till_done()
    check("disarmed in summer: 4", calls[-1], ("input_number.schema_huis", 4))
    S("calendar.feestdagen", "on"); h._tick(); await hass.async_block_till_done()
    check("holiday wins over summer: 3", calls[-1], ("input_number.schema_huis", 3))
    S("calendar.feestdagen", "off"); S("sensor.season", "autumn"); h._tick(); await hass.async_block_till_done()
    check("no rule: back to 1", calls[-1], ("input_number.schema_huis", 1))
    g["holiday_dates"] = [dt_util.now().strftime("%m-%d")]; h._tick(); await hass.async_block_till_done()
    check("own date is a holiday: 3", calls[-1], ("input_number.schema_huis", 3))
    # without a calendar set: the Holiday integration's calendar is used
    from homeassistant.helpers import entity_registry as er
    ent = er.async_get(hass).async_get_or_create("calendar", "holiday", "nl", suggested_object_id="nederland")
    g.pop("holiday_calendar"); g["holiday_dates"] = []; S(ent.entity_id, "on")
    check("Holiday integration's calendar found", HT.holiday_calendar(hass), ent.entity_id)
    h._tick(); await hass.async_block_till_done()
    check("its holiday: still 3", h.held["input_number.schema_huis"]["set"], 3)
    g["holiday_dates"] = [dt_util.now().strftime("%m-%d")]
    sit = h.situations()
    check("situations", (sit["holiday"], sit["summer"], sit["season"]), (True, False, "autumn"))
    g["holiday_dates"] = []; g["rules"] = {"armed_away": 3, "nobody": 3}; h._tick(); await hass.async_block_till_done()
    S("input_number.schema_huis", "1.0", {"min": 1, "max": 3}); h.held.clear(); calls.clear()
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
    # air conditioners: found in the area, sleep timer on the same device, outdoor unit split
    from homeassistant.helpers import device_registry as dr, area_registry as ar
    from homeassistant import config_entries
    from homeassistant.config_entries import ConfigEntry
    await ar.async_load(hass); await dr.async_load(hass)
    hass.config_entries = config_entries.ConfigEntries(hass, {}); await hass.config_entries.async_initialize()
    entry = ConfigEntry(version=1, minor_version=1, domain="lg_thinq", title="x", data={}, options={}, source="user", unique_id=None, discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    areg = ar.async_get(hass); dreg = dr.async_get(hass); ereg = er.async_get(hass)
    woon = areg.async_create("Woon")
    rooms[0]["area_id"] = woon.id
    dev1 = dreg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("lg", "ac1")}, name="LG Woon")
    dreg.async_update_device(dev1.id, area_id=woon.id)
    c1 = ereg.async_get_or_create("climate", "lg_thinq", "ac1", device_id=dev1.id, suggested_object_id="lg_woon")
    t1 = ereg.async_get_or_create("number", "lg_thinq", "ac1_sleep", device_id=dev1.id, suggested_object_id="lg_woon_sleep_timer", translation_key="sleep_timer")
    dev2 = dreg.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("lg", "ac2")}, name="LG Slaap")
    c2 = ereg.async_get_or_create("climate", "lg_thinq", "ac2", device_id=dev2.id, suggested_object_id="lg_slaap")
    S(c1.entity_id, "heat", {"hvac_action": "heating", "fan_mode": "auto", "fan_modes": ["auto", "low", "high"], "swing_mode": "off", "swing_modes": ["off", "on"]})
    S(c2.entity_id, "cool", {"hvac_action": "cooling"})
    S(t1.entity_id, "0", {"min": 0, "max": 12, "step": 1, "unit_of_measurement": "h"})
    check("devices in the area", HT.room_devices(hass, rooms[0]), [c1.entity_id])
    check("sleep timer of the same device", HT.sleep_timer(hass, c1.entity_id), t1.entity_id)
    check("device's room", HT.device_room(hass, c1.entity_id), woon.id)
    hass.data[DOMAIN]["settings"]["heating"]["outdoor"] = [{"name": "Buiten 1", "sensor": "sensor.buiten1", "units": [c1.entity_id, c2.entity_id]}]
    S("sensor.buiten1", "1.2", {"unit_of_measurement": "kW"})
    m2 = EM.EnergyMeter(hass); hass.data[DOMAIN]["meter"] = m2
    t2 = dt_util.as_utc(dt_util.as_local(dt_util.utcnow()).replace(hour=9, minute=0, second=0, microsecond=0))
    with patch.object(EM.dt_util, "utcnow", return_value=t2 + timedelta(hours=1)):
        m2.add(st, t2)
        for i in range(1, 121):
            m2.add(st, t2 + timedelta(seconds=30 * i))
        tot = m2.heat_totals(woon.id); dt = m2.device_today(woon.id, c1.entity_id)
        rs = HT.room_status(hass, woon.id)
    check("outdoor 1.2 kW split over 2 running units: 0.6 kWh each", round(dt["kwh"], 2), 0.6)
    check("heating unit counts as heat pump heat", (round(tot["day"]["kwh_hp"], 2), round(dt["heat"], 2)), (0.6, 0.6))
    check("cooling unit is not heat", round(m2.heat_totals(None)["day"]["kwh_hp"], 2), 0.6)
    g2 = rs["gas"]["day"]
    check("gas: heater 0.6 × 1 + air conditioner 0.6 × COP 3.5 = 2.7 kWh heat", round(g2["heat"], 2), 2.7)
    d0 = rs["devices"][0]
    check("device status", (d0["entity"], d0["fan"], d0["fan_modes"], d0["sleep"]["entity"], d0["sleep"]["unit"]), (c1.entity_id, "auto", ["auto", "low", "high"], t1.entity_id, "h"))
    # night settings on armed home
    svc = []
    async def rec(call): svc.append((call.domain, call.service, dict(call.data)))
    for dom, sv in (("climate", "set_fan_mode"), ("climate", "set_swing_mode"), ("number", "set_value")):
        hass.services.async_register(dom, sv, rec)
    rooms[0]["heating"]["device_night"] = {c1.entity_id: {"fan_mode": "low", "swing_mode": "off", "sleep": 2}}
    S("alarm_control_panel.a", "disarmed"); h._tick(); await hass.async_block_till_done(); svc.clear()
    S("alarm_control_panel.a", "armed_home"); h._tick(); await hass.async_block_till_done()
    check("armed home: fan low, sleep 2 h (swing already off)", sorted((x[1], list(x[2].values())[-1]) for x in svc), [("set_fan_mode", "low"), ("set_value", 2)])
    svc.clear(); h._tick(); await hass.async_block_till_done()
    check("only on the change to armed home", svc, [])
    # device time slots: set at the start, back at the end
    hass.services.async_register("climate", "set_swing_horizontal_mode", rec); hass.services.async_register("climate", "set_temperature", rec)
    S(c1.entity_id, "heat", {"hvac_action": "heating", "fan_mode": "auto", "fan_modes": ["auto", "low", "high"], "swing_mode": "off", "swing_modes": ["off", "on"],
                             "hvac_modes": ["off", "heat", "cool"], "temperature": 21})
    rooms[0]["heating"].pop("climate", None); hass.states.async_remove(f"climate.roommind_{woon.id}")
    tz = dt_util.get_default_time_zone(); day = datetime(2026, 11, 26, 22, 30, tzinfo=tz)  # Thursday
    slot = {"days": [3], "start": {"type": "time", "time": "22:00"}, "end": {"type": "time", "time": "07:00"},
            "set": {"fan_mode": "low", "swing_mode": "on", "sleep": 2, "temperature": 19}}
    rooms[0]["heating"]["device_slots"] = {c1.entity_id: [slot]}
    svc.clear(); h._device_slots(day); await hass.async_block_till_done()
    check("slot starts: fan low, swing on, 19°, sleep 2", sorted((x[1], [v for k, v in x[2].items() if k != "entity_id"][0]) for x in svc),
          [("set_fan_mode", "low"), ("set_swing_mode", "on"), ("set_temperature", 19), ("set_value", 2)])
    S(c1.entity_id, "heat", {**hass.states.get(c1.entity_id).attributes, "fan_mode": "low", "swing_mode": "on", "temperature": 19})
    svc.clear(); h._device_slots(day + timedelta(minutes=5)); await hass.async_block_till_done()
    check("still in the slot: nothing again", svc, [])
    S(c1.entity_id, "heat", {**hass.states.get(c1.entity_id).attributes, "swing_mode": "off"})  # changed by hand
    svc.clear(); h._device_slots(day + timedelta(hours=9)); await hass.async_block_till_done()
    check("slot ends (07:00 next day): fan and temperature back, swing not (changed by hand)", sorted((x[1], [v for k, v in x[2].items() if k != "entity_id"][0]) for x in svc),
          [("set_fan_mode", "auto"), ("set_temperature", 21)])
    rooms[0]["heating"]["devices"] = [c2.entity_id]
    check("devices set by hand", HT.room_devices(hass, rooms[0]), [c2.entity_id])
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
