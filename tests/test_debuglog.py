import asyncio, sys, tempfile, types
from datetime import timedelta
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
from roomcontrol.light import RoomControlLight
from roomcontrol import debug_log as D

ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))

async def boot(d, extra=None):
    hass = HomeAssistant(d); await ar.async_load(hass); await dr.async_load(hass); await er.async_load(hass); await hass.async_start()
    hass.states.async_set("sun.sun", "below_horizon", {"elevation": -10})
    hass.states.async_set("light.a", "on", {"brightness": 200, "friendly_name": "Lamp A"})
    hass.states.async_set("light.b", "off", {"friendly_name": "Lamp B"})
    hass.states.async_set("light.c", "off", {"friendly_name": "Losse lamp"})
    hass.states.async_set("person.p", "home")
    hass.states.async_set("lock.voor", "locked", {"friendly_name": "Voordeur"})
    room = {"area_id": "woonkamer", "lights": [{"entity_id": "light.a"}, {"entity_id": "light.b"}, {"entity_id": "light.c"}],
            "locks": [{"entity_id": "lock.voor"}], "switches": [{"entity_id": "switch.tv"}],
            "groups": [{"id": "g1", "name": "Plafond", "lights": ["light.a"], "own_times": True,
                        "slots": [{"name": "Avond", "days": [0,1,2,3,4,5,6], "start": {"type": "time", "time": "00:00"}, "end": {"type": "time", "time": "23:59"}}]},
                       {"id": "g2", "name": "Leeslamp", "lights": ["light.b"]}]}
    hass.data[DOMAIN] = {"rooms": [room], "settings": {}, "entities": {}, **(extra or {})}
    e = RoomControlLight(hass, "woonkamer"); e.hass = hass; e.entity_id = "light.rc_wk"; e._members = ["light.a", "light.b", "light.c"]
    await e.async_added_to_hass(); await hass.async_block_till_done()
    return hass, e

async def main():
    d = tempfile.mkdtemp()
    hass, e = await boot(d)
    e._dbg("on", "time_slot", ["light.a", "light.b"])
    e._dbg("adjust", "lux_brighter", ["light.a"], lux=9, target=80, pct=60)
    e._dbg("blocked", "motion", ["light.b"], why="armed_away")
    e._dbg("info", "manual_start", minutes=30)
    e._dbg("lock", "lock_time", device="Voordeur", item="lock.voor", time="22:40")
    from roomcontrol.room_switches import log_switches
    log_switches(hass, ["switch.tv"], "off", "switches_nobody_home")
    last = e._debug.entries
    on = [x for x in last if x["reason"] == "time_slot"][0]
    check("items", on["items"], ["group:g1", "group:g2"])
    check("bundles", on["bundles"], ["Plafond", "Leeslamp"])
    check("win slot", on["rules"]["group:g1"]["win"], "slot")
    check("rules on has slot+home+sun", all(r in on["rules"]["group:g1"]["on"] for r in ("slot", "home", "sun")), True)
    check("slot detail", on["rules"]["group:g1"]["d"].get("slot", {}).get("name"), "Avond")
    blk = [x for x in last if x["kind"] == "blocked"][0]
    check("blocked win alarm", blk["rules"]["group:g2"]["win"], "alarm")
    adj = [x for x in last if x["kind"] == "adjust"][0]
    check("lux win", adj["rules"]["group:g1"]["win"], "lux")
    lk = [x for x in last if x["kind"] == "lock"][0]
    check("lock item", (lk["items"], lk["bundles"]), (["lock.voor"], ["Voordeur"]))
    sw = [x for x in last if x["reason"] == "switches_nobody_home"][0]
    check("switch item", sw["items"], ["switch.tv"])
    items = e.debug_items()
    check("items list", [(i["key"], i["kind"]) for i in items],
          [("group:g1","bundle"),("group:g2","bundle"),("light.c","bundle"),("switch.tv","switch"),("lock.voor","lock")])
    day = e.debug_day(0, "group:g1")
    check("day g1 reasons", [x["reason"] for x in day["entries"]], ["manual_start", "lux_brighter", "time_slot"])
    check("counts g1", day["counts"][0], 3)
    check("day all", len(e.debug_day(0, None)["entries"]), len(e._debug.entries))
    # an old entry by name only (before items) and an 8 day old one
    old_at = (dt_util.utcnow() - timedelta(days=1)).isoformat()
    e._debug.append({"at": old_at, "kind": "on", "reason": "motion", "bundles": ["Plafond"]})
    check("yesterday by name", [x["reason"] for x in e.debug_day(1, "group:g1")["entries"]][:1] if dt_util.as_local(dt_util.utcnow()).hour >= 0 else None, ["motion"])
    now = e.debug_now()
    check("now key+rules", (now["bundles"][0]["key"], "win" in now["bundles"][0]["rules"]), ("group:g1", True))
    # websocket
    from roomcontrol import ws_get_debug
    class C:
        def send_result(self, i, r): self.r = r
        def send_error(self, *a): self.r = a
    c = C(); ws_get_debug.__wrapped__(hass, c, {"id": 1, "type": "roomcontrol/get_debug", "area_id": "woonkamer", "day": 0, "item": "group:g1"}) if hasattr(ws_get_debug, "__wrapped__") else ws_get_debug(hass, c, {"id": 1, "type": "roomcontrol/get_debug", "area_id": "woonkamer", "day": 0, "item": "group:g1"})
    check("ws day keys", sorted(c.r), ["counts", "entries", "items", "now", "upcoming"])
    c = C(); ws_get_debug(hass, c, {"id": 2, "type": "roomcontrol/get_debug", "area_id": "woonkamer"})
    check("ws plain no rules", any("rules" in x for x in c.r["entries"]), False)
    before = {(x["at"], x["reason"]) for x in e._debug.entries}
    await hass.async_stop(force=True)
    # restart: the log comes back from its own file; memory log (old) imported
    old = {"at": (dt_util.utcnow() - timedelta(days=8)).isoformat(), "kind": "on", "reason": "motion", "bundles": ["Plafond"]}
    class Mem:
        def get(self, k): return {"debug": [old, {"at": dt_util.utcnow().isoformat(), "kind": "info", "reason": "fromold", "bundles": []}]}
        def register(self, k, f): return lambda: None
    hass2, e2 = await boot(d, {"memory": Mem()})
    reasons = [x["reason"] for x in e2._debug.entries]
    check("all restored", before <= {(x["at"], x["reason"]) for x in e2._debug.entries}, True)
    check("old memory imported", "fromold" in reasons, True)
    check("8 days pruned", any(x["at"] == old["at"] for x in e2._debug.entries), False)
    check("memory no longer holds log", "debug" in e2._memory_data(), False)
    await hass2.async_stop(force=True)
    print("ALL OK" if ok else "SOME FAILED")
asyncio.run(main())
