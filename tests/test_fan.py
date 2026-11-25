"""Scenario test for the shared fan activity (real HA event loop, short timings)."""
import asyncio
import sys
import tempfile
import types

import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for mod in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[mod] = types.ModuleType(mod)

from homeassistant.core import HomeAssistant, ServiceCall  # noqa: E402

from roomcontrol.const import DOMAIN  # noqa: E402
from roomcontrol.light import RoomControlLight  # noqa: E402
from roomcontrol.fan_activity import fan_activities  # noqa: E402

STEP = 0.02  # minutes per step (1.2 s)
RUN_ON = 1  # seconds


def room(area, sensor, fans=(), steps=True, shared=()):
    return {
        "area_id": area,
        "motion_sensors": [sensor],
        "fans": list(fans),
        "fan_steps": [{"minutes": 0, "percentage": 33}, {"minutes": STEP, "percentage": 66},
                      {"minutes": 2 * STEP, "percentage": 100}] if steps else [],
        "fan_shared_rooms": list(shared),
        "fan_run_on": RUN_ON,
    }


def make(hass, area):
    e = RoomControlLight.__new__(RoomControlLight)
    e.hass, e._area_id, e._fan_key, e._fan_temp_pct, e._manual_until = hass, area, None, None, None
    e.entity_id = None
    hass.data[DOMAIN]["entities"][area] = e
    return e


async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await hass.async_start()
    calls = []

    async def record(call: ServiceCall):
        calls.append((call.service, call.data.get("percentage")))

    for svc in ("set_percentage", "turn_off", "turn_on"):
        hass.services.async_register("fan", svc, record)

    async def motion(entity, sensor, on):
        hass.states.async_set(sensor, "on" if on else "off")
        entity._fan_update()
        await asyncio.sleep(0.05)

    ok = True

    def check(label, cond):
        nonlocal ok
        ok &= cond
        print(("PASS " if cond else "FAIL ") + label, calls)

    # ── 1: single room, motion stops after step 1 → off after run-on ──
    hass.data[DOMAIN] = {"rooms": [room("wc", "binary_sensor.wc", ["fan.wc"])], "entities": {}}
    wc = make(hass, "wc")
    await motion(wc, "binary_sensor.wc", True)
    await asyncio.sleep(0.2)
    check("1a step 1 applied", calls == [("set_percentage", 33)])
    await motion(wc, "binary_sensor.wc", False)
    await asyncio.sleep(STEP * 60 + 0.3)  # step 2 time passes during run-on
    await asyncio.sleep(RUN_ON)
    check("1b off after run-on, no step 2", calls == [("set_percentage", 33), ("turn_off", None)])
    check("1c activity gone", not fan_activities(hass))

    # ── 2: shared fan; room B keeps motion → steps continue, off only when both quiet ──
    calls.clear()
    hass.data[DOMAIN] = {
        "rooms": [room("a", "binary_sensor.a", ["fan.shared"], shared=["b"]),
                  room("b", "binary_sensor.b", steps=False)],
        "entities": {},
    }
    a, b = make(hass, "a"), make(hass, "b")
    await motion(a, "binary_sensor.a", True)
    await asyncio.sleep(0.2)
    await motion(b, "binary_sensor.b", True)
    await motion(a, "binary_sensor.a", False)  # A empty, B occupied
    await asyncio.sleep(STEP * 60 * 2 + 0.5)
    check("2a steps continue while B occupied", calls == [("set_percentage", 33), ("set_percentage", 66),
                                                           ("set_percentage", 100)])
    check("2b no run-on while B occupied", fan_activities(hass)[("fan.shared",)].off_at is None)
    await motion(b, "binary_sensor.b", False)
    await asyncio.sleep(RUN_ON + 0.3)
    check("2c off after both quiet + run-on", calls[-1] == ("turn_off", None) and not fan_activities(hass))

    # ── 3: motion returns during run-on → no off, steps resume ──
    calls.clear()
    await motion(b, "binary_sensor.b", True)
    await asyncio.sleep(0.2)
    await motion(b, "binary_sensor.b", False)
    await asyncio.sleep(RUN_ON / 2)
    await motion(a, "binary_sensor.a", True)
    await asyncio.sleep(RUN_ON)
    check("3a no off when motion returns", ("turn_off", None) not in calls)
    act = fan_activities(hass)[("fan.shared",)]
    check("3b stand visible", a._fan_activity_attrs()["fan_step"] == act.step == b._fan_activity_attrs()["fan_step"])
    await motion(a, "binary_sensor.a", False)
    await asyncio.sleep(RUN_ON + 0.3)
    check("3c finally off", calls[-1] == ("turn_off", None))

    await hass.async_stop()
    print("ALL PASS" if ok else "SOME FAILED")


asyncio.run(main())
