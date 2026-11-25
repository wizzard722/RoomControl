import asyncio, sys, tempfile, types
from datetime import timedelta
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.light as LI
from roomcontrol.learn import LearnStore
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp())
    await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    a = ar.async_get(hass).async_create("Keuken"); b = ar.async_get(hass).async_create("Woonkamer")
    hass.states.async_set("sensor.lux", "100"); hass.states.async_set("sensor.lux2", "50"); hass.states.async_set("light.k", "on", {"brightness": 100})
    learn = LearnStore(hass)
    rk = {"area_id": a.id, "lights": [{"entity_id": "light.k"}], "lux_sensors": ["sensor.lux"], "target_lux": 300, "predict": {"lux": True}, "linked_rooms": [b.id]}
    rw = {"area_id": b.id, "lights": [], "lux_sensors": ["sensor.lux2"], "target_lux": 300}
    hass.data[DOMAIN] = {"rooms": [rk, rw], "settings": {}, "entities": {}, "learn": learn}
    e = LI.RoomControlLight(hass, a.id); e.hass = hass; e.entity_id = "light.rc_k"; e._members = ["light.k"]
    w = LI.RoomControlLight(hass, b.id); w.hass = hass; w.entity_id = "light.rc_w"; w._members = []
    hass.data[DOMAIN]["entities"] = {a.id: e, b.id: w}
    check("before learning: 30 s", e._lux_gap(), 30)
    t = dt_util.utcnow(); lux = 100.0
    clock = {"t": t}
    patch.object(LI.dt_util, "utcnow", lambda: clock["t"]).start()
    for i in range(12):
        d = "up" if i % 2 == 0 else "down"; db = 20 if d == "up" else -20
        clock["t"] = t = t + timedelta(minutes=1)
        e._lux_start_watch(t, lux, d, 2.0 * db, db)
        # 4 s: nothing yet; 8 s: the sensor shows it
        clock["t"] = t + timedelta(seconds=4); e._lux_response()
        lux += 2.0 * db; hass.states.async_set("sensor.lux", str(lux))
        clock["t"] = t + timedelta(seconds=8 + (i % 3)); e._lux_response()
    st = e._lux_stats()
    print("stats", st)
    check("12 reactions, sure", (st["n_react"], st["sure"]), (12, True))
    check("wait up = p90 + 3", st["wait"]["up"], 13)
    e._lux_last_dir = "down"
    check("gap uses the learned wait", e._lux_gap(), float(st["wait"]["down"]))
    check("gain up learned 2.0", round(learn.room(a.id)["lux"]["gain"]["up"], 1), 2.0)
    check("gain used", round(e._lux_gain_for("up"), 1), 2.0)
    # no reaction: timeout
    clock["t"] = t = t + timedelta(minutes=1)
    e._lux_start_watch(t, lux, "up", 4.0, 2)
    clock["t"] = t + timedelta(seconds=301); e._lux_timeout(clock["t"])
    check("no reaction recorded", learn.room(a.id)["lux"]["samples"][-1][2], None)
    # option off: back to 30 s
    rk["predict"] = {"lux": False}
    check("option off: 30 s", e._lux_gap(), 30)
    # linked: Keuken steps +40, Woonkamer sees +8 lux after 12 s
    clock["t"] = t = t + timedelta(minutes=1)
    e._lux_notify_linked(40, t)
    hass.states.async_set("sensor.lux2", "58"); clock["t"] = t + timedelta(seconds=12); w._lux_response()
    lk = learn.room(b.id)["lux"]["linked"][a.id]
    check("linked gain 0.2, 12 s", (lk["gain"], lk["lat"]), (0.2, 12.0))
    m = e.lux_model()
    check("model for panel", (m["n"], len(m["samples"]), m["enabled"]), (13, 13, False))
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
