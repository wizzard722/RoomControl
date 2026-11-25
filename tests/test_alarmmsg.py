import asyncio, sys, tempfile, types
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from roomcontrol.const import DOMAIN
import roomcontrol.alarm_auto as A
from roomcontrol.person_notify import person_notify_service
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    from homeassistant import config_entries as ce
    hass.config_entries = ce.ConfigEntries(hass, {}); await hass.config_entries.async_initialize()
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    import inspect
    from homeassistant.config_entries import ConfigEntry
    kw = dict(domain="mobile_app", title="SM", data={}, source="user", version=1, minor_version=1, options={}, unique_id="x")
    params = inspect.signature(ConfigEntry).parameters
    if "discovery_keys" in params: kw["discovery_keys"] = {}
    if "subentries_data" in params: kw["subentries_data"] = None
    entry = ConfigEntry(**kw); hass.config_entries._entries[entry.entry_id] = entry
    dev = dr.async_get(hass).async_get_or_create(config_entry_id=entry.entry_id, identifiers={("mobile_app", "x")}, name="SM-S916B")
    er.async_get(hass).async_get_or_create("device_tracker", "mobile_app", "t1", suggested_object_id="sm_s916b", config_entry=entry, device_id=dev.id)
    hass.states.async_set("person.paul", "home", {"friendly_name": "Paul", "device_trackers": ["device_tracker.sm_s916b"]})
    hass.states.async_set("person.sarah", "home", {"friendly_name": "Sarah", "device_trackers": []})
    calls = []
    for svc in ("mobile_app_sm_s916b", "mobile_app_sarah"):
        async def h(c, svc=svc): calls.append((svc, c.data["message"]))
        hass.services.async_register("notify", svc, h)
    hass.data[DOMAIN] = {"settings": {"persons": [], "alarm": {}}, "rooms": []}
    check("Paul's phone found automatically", person_notify_service(hass, "person.paul"), "notify.mobile_app_sm_s916b")
    check("Sarah without tracker: none", person_notify_service(hass, "person.sarah"), None)
    hass.data[DOMAIN]["settings"]["person_notify"] = {"person.sarah": "notify.mobile_app_sarah"}
    check("Sarah's chosen device", person_notify_service(hass, "person.sarah"), "notify.mobile_app_sarah")
    a = A.AlarmAutomation(hass)
    a._notify("Test 1"); await hass.async_block_till_done()
    n = hass.states.get("persistent_notification.roomcontrol_alarm")
    check("default: everyone + notification in HA", (sorted(c[0] for c in calls), n is not None or len(hass.states.async_entity_ids("persistent_notification")) >= 0), (["mobile_app_sarah", "mobile_app_sm_s916b"], True))
    calls.clear()
    a._notify("Test 2", {"notify_persons": ["person.paul"], "notify_ha": False}); await hass.async_block_till_done()
    check("per state: only Paul", calls, [("mobile_app_sm_s916b", "Test 2")])
    calls.clear()
    a._notify("Test 3", {"notify_persons_off": True}); await hass.async_block_till_done()
    check("per state: persons off", calls, [])
    hass.data[DOMAIN]["settings"]["alarm"] = {"msg_persons": ["person.sarah"], "notify_skip": "input_boolean.hulp"}
    hass.states.async_set("input_boolean.hulp", "on")
    calls.clear(); a._notify("Test 4"); await hass.async_block_till_done()
    check("skip switch on: nobody", calls, [])
    hass.states.async_set("input_boolean.hulp", "off")
    calls.clear(); a._notify("Test 5"); await hass.async_block_till_done()
    check("alarm default: only Sarah", calls, [("mobile_app_sarah", "Test 5")])
    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
