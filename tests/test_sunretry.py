import asyncio, sys, tempfile, types
from datetime import timedelta, datetime
from unittest.mock import patch
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components"))
for m in ("homeassistant.components.panel_custom", "homeassistant.components.frontend"):
    sys.modules[m] = types.ModuleType(m)
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from roomcontrol.const import DOMAIN
import roomcontrol.energy as EN, roomcontrol.solar_forecast as SF
ok = True
def check(label, got, want):
    global ok; ok &= got == want; print(("PASS " if got == want else "FAIL ") + f"{label}: {got}" + ("" if got == want else f" (want {want})"))
async def main():
    hass = HomeAssistant(tempfile.mkdtemp()); await hass.async_start()
    hass.data[DOMAIN] = {"settings": {"energy": {"solar_forecast": ["abc"]}}, "rooms": []}
    calls = []; ready = {"v": False}
    async def fake(h, ids):
        calls.append(1)
        t = dt_util.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
        return {t: 1500.0} if ready["v"] else {}
    patch.object(SF, "async_read", fake).start()
    cls = [v for v in vars(EN).values() if isinstance(v, type) and hasattr(v, "async_refresh_sun")][0]
    patch.object(cls, "status", lambda self: {}).start()
    e = cls(hass)
    now = dt_util.utcnow()
    clock = {"t": now}
    patch.object(EN.dt_util, "utcnow", lambda: clock["t"]).start()
    async def tick(): e._tick(); await hass.async_block_till_done()
    await tick(); check("first read", len(calls), 1)
    clock["t"] += timedelta(seconds=30); await tick(); check("30 s later: not yet", len(calls), 1)
    clock["t"] += timedelta(seconds=40); await tick(); check("empty → again after a minute", len(calls), 2)
    check("not missing yet", e.sun_missing(), False)
    for _ in range(31):
        clock["t"] += timedelta(minutes=1); await tick()
    check("missing after 30 min", e.sun_missing(), True)
    ready["v"] = True; clock["t"] += timedelta(minutes=1); await tick()
    check("got it: not missing", (bool(e.sun), e.sun_missing()), (True, False))
    n = len(calls); clock["t"] += timedelta(minutes=5); await tick()
    check("with data: back to 15 min", len(calls), n)
    clock["t"] += timedelta(minutes=11); await tick(); check("after 16 min: refreshed", len(calls), n + 1)
    await hass.async_stop(); print("ALL PASS" if ok else "SOME FAILED")
asyncio.run(main())
