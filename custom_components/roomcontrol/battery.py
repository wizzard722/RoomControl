"""Home battery (energy step 6): simulation and control.

General setting "energy" → "battery":
 {"soc_sensor": sensor (%), "power_sensor": sensor (W),
  "power_sign": "charge_positive" | "discharge_positive",
  "control": "number" | "select" | "scripts",
  "number_entity": number (W setpoint; with "select" the power to use),
  "number_sign": "charge_positive" | "discharge_positive",
  "select_entity": select, "options": {"charge", "discharge", "self", "idle": option},
  "scripts": {"charge", "discharge", "self", "idle": script}  # get variable "power" (W)
  "capacity_kwh": 5, "max_charge_kw": 2.4, "max_discharge_kw": 2.4,
  "efficiency": 90 (round trip, %), "soc_min": 10, "soc_max": 100,
  "reserve": 20 (%, kept for a power cut), "wear": 0.03 (€ per kWh discharged),
  "strategy": "off" | "self" | "price", "grid_charge": bool, "to_car": bool}

Simulation ("what would a battery bring?"): the house's hours of the last
days from RoomControl's own phase sensors (hourly means from Home Assistant's
statistics: consumed = taken from the grid, produced = returned), checked
against the Energy dashboard's grid meters (how well they match). Prices per
hour: what offpay.py keeps (the price you pay), the feed-in price derived
from it as in the energy contract. Each battery is run hour by hour:
- "none": no battery;
- "self": the maker's own mode (charge with surplus, discharge for use);
- "price": RoomControl's plan per day (dynamic programming over the battery
  level), with grid charging when that pays after losses and wear.

Control: every 15 minutes a plan for the next 24 hours (the same optimiser,
per quarter: expected use per hour of the day minus the solar forecast, the
prices). Each quarter becomes an action: "charge" (from the grid), "idle"
(keep the level for dearer hours), "discharge" (feed in at a high price) or
"self" (the battery covers use and stores surplus). RoomControl sends a
command only when the action or the power changes.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import math
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

DEFAULTS = {"capacity_kwh": 5.0, "max_charge_kw": 2.4, "max_discharge_kw": 2.4, "efficiency": 90.0,
            "soc_min": 10.0, "soc_max": 100.0, "reserve": 20.0, "wear": 0.03}
SIM_SIZES = [{"kwh": 5.0, "kw": 2.4}, {"kwh": 10.0, "kw": 3.6}]
STEPS = 40  # battery levels in the optimiser
ACTIONS = ("charge", "discharge", "self", "idle")


def _energy(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    cfg = _energy(hass).get("battery")
    return cfg if isinstance(cfg, dict) else {}


def _num(value: Any, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def params(cfg: dict[str, Any], kwh: float | None = None, kw: float | None = None) -> dict[str, float]:
    """The battery's numbers (defaults filled in): capacity, power, efficiency per way, level range."""
    p = {k: _num(cfg.get(k), v) for k, v in DEFAULTS.items()}
    if kwh is not None:
        p["capacity_kwh"] = kwh
    if kw is not None:
        p["max_charge_kw"] = p["max_discharge_kw"] = kw
    eta = math.sqrt(max(0.5, min(1.0, p["efficiency"] / 100)))
    cap = p["capacity_kwh"]
    low = cap * max(p["soc_min"], p["reserve"]) / 100
    high = cap * max(0.0, min(100.0, p["soc_max"])) / 100
    return {**p, "eta": eta, "low": min(low, high), "high": high}


# ── the battery models ─────────────────────────────────────────────────────


def _step_cost(net: float, c: float, d: float, buy: float, sell: float, wear: float) -> float:
    grid = net + c - d
    return (buy * grid if grid > 0 else sell * grid) + wear * d


def run_self(steps: list[tuple[float, float, float]], p: dict[str, float], dt: float, soc: float) -> tuple[float, float, list[float]]:
    """The maker's own mode: charge with surplus, discharge for use. → (cost, end level, grid-side flows)."""
    cost, flows = 0.0, []
    for net, buy, sell in steps:
        c = d = 0.0
        if net < 0:
            c = min(-net, p["max_charge_kw"] * dt, max(0.0, (p["high"] - soc) / p["eta"]))
            soc += c * p["eta"]
        elif net > 0:
            d = min(net, p["max_discharge_kw"] * dt, max(0.0, (soc - p["low"]) * p["eta"]))
            soc -= d / p["eta"]
        flows.append(c - d)
        cost += _step_cost(net, c, d, buy, sell, p["wear"])
    return cost, soc, flows


def optimise(steps: list[tuple[float, float, float]], p: dict[str, float], dt: float, soc0: float,
             grid_charge: bool = True) -> tuple[float, float, list[float], list[float]]:
    """Best use of the battery over these steps (net use kWh, buy, sell), by
    dynamic programming over STEPS levels. The level left at the end is worth
    the cheapest buy price (after losses), so it is not dumped.
    → (cost, end level, grid-side flows (+ charge, − discharge), levels)."""
    low, high = p["low"], p["high"]
    if high - low <= 1e-6 or not steps:
        cost, soc, flows = run_self(steps, p, dt, soc0)
        return cost, soc, flows, [soc0] * len(steps)
    levels = [low + (high - low) * i / STEPS for i in range(STEPS + 1)]
    start = min(range(len(levels)), key=lambda i: abs(levels[i] - soc0))
    max_c, max_d, eta, wear = p["max_charge_kw"] * dt, p["max_discharge_kw"] * dt, p["eta"], p["wear"]
    terminal = min(b for _n, b, _s in steps) * eta
    n = len(steps)
    inf = float("inf")
    best = [lvl * terminal * -1 for lvl in levels]  # value-to-go at the end (negative cost)
    choice: list[list[int]] = [[0] * len(levels) for _ in range(n)]
    for t in range(n - 1, -1, -1):
        net, buy, sell = steps[t]
        new = [inf] * len(levels)
        surplus = max(0.0, -net)
        for i, a in enumerate(levels):
            row_best, row_j = inf, i
            for j, b in enumerate(levels):
                delta = b - a
                if delta > 0:
                    c, d = delta / eta, 0.0
                    if c > max_c + 1e-9 or (not grid_charge and c > surplus + 1e-9):
                        continue
                else:
                    c, d = 0.0, -delta * eta
                    if d > max_d + 1e-9:
                        continue
                v = _step_cost(net, c, d, buy, sell, wear) + best[j]
                if v < row_best:
                    row_best, row_j = v, j
            new[i], choice[t][i] = row_best, row_j
        best = new
    flows, path, cost, i = [], [], 0.0, start
    soc = levels[start]
    for t in range(n):
        j = choice[t][i]
        delta = levels[j] - levels[i]
        c, d = (delta / eta, 0.0) if delta > 0 else (0.0, -delta * eta)
        cost += _step_cost(steps[t][0], c, d, steps[t][1], steps[t][2], wear)
        flows.append(c - d)
        soc = levels[j]
        path.append(soc)
        i = j
    return cost, soc, flows, path


def simulate(hours: list[dict[str, Any]], p: dict[str, float], grid_charge: bool = True) -> dict[str, float]:
    """Hours [{"t": datetime, "imp": kWh, "exp": kWh, "buy": €, "sell": €}] → cost
    without a battery, with the maker's own mode and with RoomControl's plan."""
    none = sum(h["imp"] * h["buy"] - h["exp"] * h["sell"] for h in hours)
    days: dict[str, list[dict[str, Any]]] = {}
    for h in hours:
        days.setdefault(dt_util.as_local(h["t"]).strftime("%Y-%m-%d"), []).append(h)
    soc_self = soc_opt = p["low"]
    self_cost = opt_cost = 0.0
    cycled = 0.0
    for day in sorted(days):
        steps = [(h["imp"] - h["exp"], h["buy"], h["sell"]) for h in days[day]]
        c, soc_self, _f = run_self(steps, p, 1.0, soc_self)
        self_cost += c
        c, soc_opt, flows, _path = optimise(steps, p, 1.0, soc_opt, grid_charge)
        opt_cost += c
        cycled += sum(-f for f in flows if f < 0)
    return {"none": round(none, 2), "self": round(self_cost, 2), "price": round(opt_cost, 2),
            "cycles": round(cycled / max(0.1, p["capacity_kwh"]), 1)}


# ── the data for the simulation ────────────────────────────────────────────


async def _stats(hass: HomeAssistant, ids: set[str], start: datetime, end: datetime, kind: str) -> dict[str, list[dict[str, Any]]]:
    if not ids:
        return {}
    try:
        from homeassistant.components.recorder import get_instance  # noqa: PLC0415
        from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415

        return await get_instance(hass).async_add_executor_job(
            statistics_during_period, hass, start, end, ids, "hour", None, {kind})
    except Exception as err:  # noqa: BLE001 - no recorder, or old HA
        _LOGGER.debug("Battery simulation: no statistics: %s", err)
        return {}


def _kw_factor(hass: HomeAssistant, sensor: str) -> float:
    """W → kWh per hour is /1000; a sensor in kW is taken as it is."""
    st = hass.states.get(sensor)
    unit = str(st.attributes.get("unit_of_measurement", "W") if st else "W").lower()
    return 1.0 if unit == "kw" else 0.001


async def _dashboard_grid(hass: HomeAssistant) -> tuple[list[str], list[str]]:
    try:
        from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

        manager = await async_get_manager(hass)
        sources = (manager.data or {}).get("energy_sources") or []
    except Exception:  # noqa: BLE001 - no Energy dashboard
        return [], []
    imp, exp = [], []
    for src in sources:
        if src.get("type") != "grid":
            continue
        imp += [f["stat_energy_from"] for f in src.get("flow_from") or [] if f.get("stat_energy_from")]
        exp += [f["stat_energy_to"] for f in src.get("flow_to") or [] if f.get("stat_energy_to")]
        if src.get("stat_energy_from"):
            imp.append(src["stat_energy_from"])
        if src.get("stat_energy_to"):
            exp.append(src["stat_energy_to"])
    return imp, exp


async def async_hours(hass: HomeAssistant, days: int) -> dict[str, Any]:
    """The house's hours: import and export (kWh) and the prices, with where they came from."""
    from .offpay import hour_key  # noqa: PLC0415
    from .tariff import VAT, _cfg as contract  # noqa: PLC0415

    energy = _energy(hass)
    end = dt_util.utcnow().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    used = {s for s in (energy.get("phase_sensors") or {}).values() if s}
    back = {s for s in (energy.get("produced_sensors") or {}).values() if s}
    per: dict[datetime, dict[str, float]] = {}
    source = None
    stats = await _stats(hass, used | back, start, end, "mean")
    if stats:
        source = "roomcontrol"
        for sensor, rows in stats.items():
            f = _kw_factor(hass, sensor)
            key = "imp" if sensor in used else "exp"
            for r in rows:
                if r.get("mean") is None:
                    continue
                t = dt_util.utc_from_timestamp(r["start"]) if isinstance(r["start"], (int, float)) else r["start"]
                per.setdefault(t, {"imp": 0.0, "exp": 0.0})[key] += max(0.0, r["mean"] * f)
    d_imp, d_exp = await _dashboard_grid(hass)
    dash: dict[datetime, dict[str, float]] = {}
    dstats = await _stats(hass, set(d_imp) | set(d_exp), start, end, "change")
    for sensor, rows in dstats.items():
        key = "imp" if sensor in d_imp else "exp"
        for r in rows:
            if r.get("change") is None:
                continue
            t = dt_util.utc_from_timestamp(r["start"]) if isinstance(r["start"], (int, float)) else r["start"]
            dash.setdefault(t, {"imp": 0.0, "exp": 0.0})[key] += max(0.0, r["change"])
    if not per and dash:
        per, source = dash, "dashboard"
    match = None
    common = [t for t in per if t in dash]
    if source == "roomcontrol" and common:
        a = sum(per[t]["imp"] + per[t]["exp"] for t in common)
        b = sum(dash[t]["imp"] + dash[t]["exp"] for t in common)
        match = round(max(0.0, 100 - abs(a - b) / b * 100)) if b > 0 else None
    # Prices per hour (the price you pay), the feed-in price derived from it.
    offpay = hass.data.get(DOMAIN, {}).get("offpay")
    prices: dict[str, float] = dict(getattr(offpay, "prices", {}) or {})
    by_hour: dict[int, list[float]] = {}
    for k, v in prices.items():
        by_hour.setdefault(int(k[-2:]), []).append(v)
    typical = {h: sorted(v)[len(v) // 2] for h, v in by_hour.items()}
    fallback = sorted(prices.values())[len(prices) // 2] if prices else _num(contract(hass).get("price_kwh"), 0.25)
    c = contract(hass)
    source_sell = c.get("market_source")

    def sell_of(buy: float) -> float:
        if source_sell == "fixed":
            return _num(c.get("feed_in_kwh"), 0.0) - _num(c.get("feed_in_cost_kwh"), 0.0)
        return buy / VAT - _num(c.get("energy_tax_kwh"), 0.1088) - _num(c.get("buy_markup_kwh"), 0.02) - _num(c.get("feed_in_cost_kwh"), 0.0)

    hours, priced = [], 0
    for t in sorted(per):
        key = hour_key(t)
        buy = prices.get(key)
        if buy is not None:
            priced += 1
        else:
            buy = typical.get(dt_util.as_local(t).hour, fallback)
        hours.append({"t": t, "imp": per[t]["imp"], "exp": per[t]["exp"], "buy": buy, "sell": sell_of(buy)})
    return {"hours": hours, "source": source, "match": match, "dashboard": bool(d_imp or d_exp),
            "priced_pct": round(priced / len(hours) * 100) if hours else 0,
            "days": round(len(hours) / 24, 1)}


# ── control ────────────────────────────────────────────────────────────────


class HomeBattery:
    """Plans and steers the home battery; runs the simulation on request."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.battery")
        self.months: dict[str, float] = {}  # month → € the battery brought (measured)
        self.profile: dict[str, float] = {}  # hour of the day → expected net use (kWh)
        self.sim: dict[str, Any] | None = None
        self.plan: list[dict[str, Any]] = []
        self._planned_at: datetime | None = None
        self._sent: tuple[str, int] | None = None
        self._test_until: datetime | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._last: datetime | None = None
        self._busy = False

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.months = {k: float(v) for k, v in (data.get("months") or {}).items() if isinstance(v, (int, float))}
        self.profile = {k: float(v) for k, v in (data.get("profile") or {}).items() if isinstance(v, (int, float))}
        self.sim = data.get("sim") if isinstance(data.get("sim"), dict) else None

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"months": self.months, "profile": self.profile, "sim": self.sim}, 30)

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=1)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._config_changed))

    @callback
    def shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []

    @callback
    def _config_changed(self, *_: Any) -> None:
        self._planned_at = None
        self._sent = None

    def configured(self) -> bool:
        cfg = _cfg(self.hass)
        return bool(cfg.get("soc_sensor")) and bool(cfg.get("number_entity") or cfg.get("select_entity") or cfg.get("scripts"))

    # ── live values ────────────────────────────────────────────────────────

    def _float(self, entity: str | None) -> float | None:
        st = self.hass.states.get(entity) if entity else None
        try:
            return float(st.state) if st is not None else None
        except (TypeError, ValueError):
            return None

    def soc_kwh(self) -> float | None:
        pct = self._float(_cfg(self.hass).get("soc_sensor"))
        return None if pct is None else pct / 100 * params(_cfg(self.hass))["capacity_kwh"]

    def power_w(self) -> float | None:
        """+ charging, − discharging."""
        cfg = _cfg(self.hass)
        value = self._float(cfg.get("power_sensor"))
        if value is None:
            return None
        if str((self.hass.states.get(cfg["power_sensor"]).attributes.get("unit_of_measurement") or "")).lower() == "kw":
            value *= 1000
        return value if cfg.get("power_sign", "charge_positive") == "charge_positive" else -value

    def _house_net_w(self) -> float | None:
        """What the house takes from the grid now (− = returning), all phases."""
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        detail = ((getattr(energy, "last_status", None) or {}).get("phase_detail") or {}) if energy else {}
        if not detail or any(d.get("consumed") is None for d in detail.values()):
            return None
        return sum(d["consumed"] for d in detail.values()) - sum(d.get("produced") or 0 for d in detail.values())

    # ── the plan ───────────────────────────────────────────────────────────

    def _quarters(self) -> list[dict[str, Any]]:
        from .solar_forecast import sun_kw_at  # noqa: PLC0415
        from .tariff import buy_now, forecast  # noqa: PLC0415

        now = dt_util.utcnow()
        start = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
        fc = forecast(self.hass)
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        sun = getattr(energy, "sun", None) or []
        fixed = buy_now(self.hass)
        out, t = [], start
        while t < start + timedelta(hours=24):
            row = next((r for r in fc if r["start"] <= t < r["end"]), None)
            if row is None and fixed is None:
                break
            hour = str(dt_util.as_local(t).hour)
            use = self.profile.get(hour, 0.3) / 4  # kWh in the quarter (net, without the sun forecast)
            sun_kwh = (sun_kw_at(sun, t, t + timedelta(minutes=15)) if sun else 0.0) / 4
            buy = row["buy"] if row else fixed
            sell = (row or {}).get("sell")
            out.append({"start": t, "net": use - sun_kwh, "buy": buy, "sell": sell if sell is not None else 0.0})
            t += timedelta(minutes=15)
        return out

    def make_plan(self) -> None:
        cfg = _cfg(self.hass)
        p = params(cfg)
        q = self._quarters()
        soc = self.soc_kwh()
        if not q or soc is None:
            self.plan = []
            return
        steps = [(r["net"], r["buy"], r["sell"]) for r in q]
        _cost, _end, flows, path = optimise(steps, p, 0.25, soc, bool(cfg.get("grid_charge", True)))
        plan = []
        for r, f, lvl in zip(q, flows, path, strict=True):
            surplus = max(0.0, -r["net"])
            use = max(0.0, r["net"])
            if f > surplus + 0.01:
                action, power = "charge", round(f / 0.25 * 1000)
            elif f < -(use + 0.01):
                action, power = "discharge", round(-f / 0.25 * 1000)
            elif f <= 0.01 and use > 0.01 and -f < use * 0.5:
                action, power = "idle", 0
            else:
                action, power = "self", 0
            plan.append({"start": r["start"].isoformat(), "action": action, "power": power,
                         "soc": round(lvl / max(0.01, p["capacity_kwh"]) * 100), "buy": round(r["buy"], 4),
                         "sell": round(r["sell"], 4)})
        self.plan = plan

    def blocks(self) -> list[dict[str, Any]]:
        """The plan as stretches of one action, with the reason's numbers."""
        out: list[dict[str, Any]] = []
        for i, q in enumerate(self.plan):
            end = (dt_util.parse_datetime(q["start"]) + timedelta(minutes=15)).isoformat()
            if out and out[-1]["action"] == q["action"]:
                out[-1].update(end=end, soc_end=q["soc"])
                out[-1]["kwh"] += q["power"] / 1000 * 0.25
                continue
            out.append({"action": q["action"], "start": q["start"], "end": end,
                        "kwh": q["power"] / 1000 * 0.25, "soc_end": q["soc"], "soc_start": self.plan[i - 1]["soc"] if i else q["soc"]})
        # average buy price per block and the dearest stretch after it
        for b in out:
            qs = [q for q in self.plan if b["start"] <= q["start"] < b["end"]]
            b["price"] = round(sum(q["buy"] for q in qs) / max(1, len(qs)), 4)
            later = [q for q in self.plan if q["start"] >= b["end"]]
            if later:
                top = max(later, key=lambda q: q["buy"])
                b["later_price"], b["later_at"] = top["buy"], top["start"]
            b["kwh"] = round(b["kwh"], 2)
        return out

    # ── steering ───────────────────────────────────────────────────────────

    async def _command(self, action: str, power: int) -> None:
        cfg = _cfg(self.hass)
        control = cfg.get("control") or ("number" if cfg.get("number_entity") else "select" if cfg.get("select_entity") else "scripts")
        try:
            if control == "scripts":
                script = (cfg.get("scripts") or {}).get(action)
                if script:
                    await self.hass.services.async_call("script", "turn_on", {"entity_id": script, "variables": {"power": power}}, blocking=False)
                return
            if control == "select" and cfg.get("select_entity"):
                option = (cfg.get("options") or {}).get(action)
                if option:
                    await self.hass.services.async_call("select", "select_option", {"entity_id": cfg["select_entity"], "option": option}, blocking=True)
                if cfg.get("number_entity") and action in ("charge", "discharge"):
                    await self.hass.services.async_call("number", "set_value", {"entity_id": cfg["number_entity"], "value": power}, blocking=True)
                return
            if cfg.get("number_entity"):
                signed = power if action == "charge" else -power if action == "discharge" else 0
                if cfg.get("number_sign") == "discharge_positive":
                    signed = -signed
                domain = cfg["number_entity"].split(".", 1)[0]
                await self.hass.services.async_call(domain, "set_value", {"entity_id": cfg["number_entity"], "value": signed}, blocking=True)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Home battery: command %s %s W failed: %s", action, power, err)

    def _self_power(self) -> tuple[str, int]:
        """Own-use mode for a battery steered by a number only: follow the house."""
        p = params(_cfg(self.hass))
        net = self._house_net_w()
        own = self.power_w() or 0.0
        if net is None:
            return "idle", 0
        need = net + own  # what the house would take without the battery
        if need < 0:
            return "charge", int(min(-need, p["max_charge_kw"] * 1000) // 50 * 50)
        return "discharge", int(min(need, p["max_discharge_kw"] * 1000) // 50 * 50)

    async def async_test(self, action: str, power: int) -> None:
        self._test_until = dt_util.utcnow() + timedelta(minutes=1)
        self._sent = None
        await self._command(action, power)

        @callback
        def _back(_now: Any) -> None:
            self._test_until = None
            self._sent = None
            self.hass.async_create_task(self._command("self", 0))

        async_call_later(self.hass, 60, _back)

    @callback
    def _tick(self, _now: Any = None) -> None:
        from .const import energy_enabled  # noqa: PLC0415

        if not energy_enabled(self.hass):
            if self._sent is not None and self.configured():
                self._sent = None
                self.hass.async_create_task(self._command("self", 0))  # back to its own mode
            self._last = None
            return
        now = dt_util.utcnow()
        self._measure(now)
        cfg = _cfg(self.hass)
        if not self.configured() or self._test_until is not None:
            return
        strategy = cfg.get("strategy") or "off"
        if strategy == "off":
            return
        if strategy == "price" and (self._planned_at is None or now - self._planned_at >= timedelta(minutes=15)):
            self.make_plan()
            self._planned_at = now
        action, power = "self", 0
        if strategy == "price" and self.plan:
            key = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0).isoformat()
            q = next((x for x in self.plan if x["start"] == key), None)
            if q is not None:
                action, power = q["action"], q["power"]
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        car = ((getattr(energy, "last_status", None) or {}).get("car") or {}) if energy else {}
        if car.get("charging") and not cfg.get("to_car") and action in ("self", "discharge"):
            action, power = "idle", 0  # the battery is not emptied into the car
        control = cfg.get("control") or ("number" if cfg.get("number_entity") else "select")
        if control == "number" and action == "self":
            action, power = self._self_power()
        if self._sent is not None and self._sent[0] == action and abs(self._sent[1] - power) < 100:
            return
        self._sent = (action, power)
        self.hass.async_create_task(self._command(action, power))

    def _measure(self, now: datetime) -> None:
        """What the battery brought (its flows at the price they replaced), and the use profile."""
        from .tariff import buy_now, sell_now  # noqa: PLC0415

        last, self._last = self._last, now
        net = self._house_net_w()
        if net is not None and now.minute % 15 == 0:
            hour = str(dt_util.as_local(now).hour)
            own = self.power_w() or 0.0
            kwh = (net + own) / 1000  # the house without the battery, kWh per hour
            old = self.profile.get(hour)
            self.profile[hour] = round(kwh if old is None else old + 0.1 * (kwh - old), 3)
            self._save()
        power = self.power_w()
        if last is None or power is None or net is None:
            return
        hours = (now - last).total_seconds() / 3600
        if hours <= 0 or hours > 0.2:
            return
        buy, sell = buy_now(self.hass), sell_now(self.hass)
        if buy is None:
            return
        sell = sell if sell is not None else 0.0
        kwh = power / 1000 * hours
        replaced = buy if net > 0 else sell  # the house takes from the grid: the battery replaces buying
        wear = params(_cfg(self.hass))["wear"]
        value = -kwh * replaced - (wear * -kwh if kwh < 0 else 0.0)
        month = dt_util.as_local(now).strftime("%Y-%m")
        self.months[month] = round(self.months.get(month, 0.0) + value, 4)

    # ── the simulation ─────────────────────────────────────────────────────

    async def async_simulate(self, days: int = 90, sizes: list[dict[str, float]] | None = None,
                             price: float | None = None) -> dict[str, Any]:
        if self._busy:
            return self.sim or {"busy": True}
        self._busy = True
        try:
            data = await async_hours(self.hass, days)
            cfg = _cfg(self.hass)
            hours = data.pop("hours")
            rows = []
            grid_charge = bool(cfg.get("grid_charge", True))
            for size in sizes or SIM_SIZES:
                p = params(cfg, size.get("kwh"), size.get("kw"))
                res = await self.hass.async_add_executor_job(simulate, hours, p, grid_charge) if hours else None
                if res is None:
                    rows.append({**size})
                    continue
                span = max(1.0, len(hours) / 24)
                saved_self, saved_price = res["none"] - res["self"], res["none"] - res["price"]
                year = saved_price * 365 / span
                rows.append({**size, **res, "saved_self": round(saved_self, 2), "saved_price": round(saved_price, 2),
                             "year_self": round(saved_self * 365 / span), "year_price": round(year),
                             "payback": round(size["price"] / year, 1) if size.get("price") and year > 0 else None})
            self.sim = {**data, "at": dt_util.utcnow().isoformat(), "rows": rows, "period": days}
            self._save()
            return self.sim
        finally:
            self._busy = False

    def status(self) -> dict[str, Any]:
        cfg = _cfg(self.hass)
        soc = self._float(cfg.get("soc_sensor"))
        month = dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m")
        if (cfg.get("strategy") == "price") and self.configured() and not self.plan:
            self.make_plan()
        return {"configured": self.configured(), "soc": soc, "power": self.power_w(),
                "strategy": cfg.get("strategy") or "off", "sent": list(self._sent) if self._sent else None,
                "plan": self.plan if cfg.get("strategy") == "price" else [],
                "blocks": self.blocks() if cfg.get("strategy") == "price" else [],
                "month": round(self.months.get(month, 0.0), 2) if month in self.months else None,
                "sim": self.sim, "params": params(cfg)}
