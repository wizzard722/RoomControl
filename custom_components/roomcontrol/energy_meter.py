"""Energy → Overzicht (step 7a): what the house uses, now and today, and where.

On every energy tick (energy.py, every 30 s) the power now is added up into
kWh: per room (its parts), the house (all phases), taken from and returned to
the grid, the solar panels, the car, and "not assigned" (the house minus the
rooms and the car). Per local day those kWh are kept with their cost (the
price you pay at that moment; what is returned at the feed-in price), for
400 days (store "roomcontrol.energy_meter"). Per room a running total feeds
the room's energy sensor (kWh, for Home Assistant's Energy dashboard →
Individual devices).

Base load ("sluipverbruik"): each night 03:00–05:00 the house's average
power and that of each metered part, the last 7 nights averaged.

General setting "energy" → "fuse_a": the main fuse per phase (default 25 A),
for the phase bars.

Energy → Rekening (step 7b), general setting "energy" → "bill":
 {"termijn": € a month (the advance payment),
  "fixed_month": € a month (standing charges, grid costs, minus the energy
                 tax rebate; may be negative),
  "gas_price": € per m³}
A month = electricity (per day: taken × the price then − returned × the
feed-in price then) + the fixed costs (per day of the month) + gas (the gas
meter of Home Assistant's Energy dashboard, m³ per day × the gas price).
The forecast for the whole month: so far plus the average day of the last
14 days for each day still to come.
"""
from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

SIGNAL_METER = f"{DOMAIN}_energy_meter"
KEEP_DAYS = 400
NIGHT = (3, 5)  # local hours of the base load window
VOLT = 230.0
DEFAULT_FUSE = 25.0


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}


def _add(d: dict[str, float], key: str, value: float) -> None:
    d[key] = round(d.get(key, 0.0) + value, 5)


class EnergyMeter:
    """Adds the power of each energy tick up into kWh and cost per day."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.energy_meter")
        self.days: dict[str, dict[str, Any]] = {}
        self.totals: dict[str, float] = {}  # area → kWh ever (the room energy sensors)
        self.nights: dict[str, dict[str, Any]] = {}  # date → {"n", "house", "parts": {key: W}, "names"}
        self._last: datetime | None = None
        self._unsub: CALLBACK_TYPE | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.days = {k: v for k, v in (data.get("days") or {}).items() if isinstance(v, dict)}
        self.totals = {k: float(v) for k, v in (data.get("totals") or {}).items() if isinstance(v, (int, float))}
        self.nights = {k: v for k, v in (data.get("nights") or {}).items() if isinstance(v, dict)}

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"days": self.days, "totals": self.totals, "nights": self.nights}, 120)

    @callback
    def start(self) -> None:
        from .energy import SIGNAL_ENERGY  # noqa: PLC0415

        self._unsub = async_dispatcher_connect(self.hass, SIGNAL_ENERGY, self._on_energy)

    @callback
    def shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ── adding up ──────────────────────────────────────────────────────────

    @callback
    def _on_energy(self, *_: Any) -> None:
        energy = self.hass.data.get(DOMAIN, {}).get("energy")
        status = getattr(energy, "last_status", None) if energy else None
        if status:
            self.add(status, dt_util.utcnow())

    def add(self, status: dict[str, Any], now: datetime) -> None:
        from .tariff import buy_now, sell_now  # noqa: PLC0415

        last, self._last = self._last, now
        if last is None:
            return
        hours = (now - last).total_seconds() / 3600
        if hours <= 0 or hours > 0.05:  # more than 3 minutes: a gap (restart), not counted
            return
        buy = buy_now(self.hass)
        sell = sell_now(self.hass)
        local = dt_util.as_local(now)
        day = self.days.setdefault(local.strftime("%Y-%m-%d"), {"rooms": {}, "rooms_cost": {}})
        rooms = status.get("rooms") or {}
        rooms_w = 0.0
        for area, r in rooms.items():
            w = r.get("watts") or 0.0
            rooms_w += w
            kwh = w / 1000 * hours
            _add(day["rooms"], area, kwh)
            if buy is not None:
                _add(day["rooms_cost"], area, kwh * buy)
            self.totals[area] = round(self.totals.get(area, 0.0) + kwh, 5)
        detail = status.get("phase_detail") or {}
        phases = [v for v in (status.get("phases") or {}).values() if v is not None]
        house_w = sum(phases) if phases and len(phases) == len(status.get("phases") or {}) else None
        car = status.get("car") or {}
        car_w = (car.get("kw") or 0.0) * 1000 if car.get("charging") else 0.0
        if house_w is not None:
            _add(day, "house", house_w / 1000 * hours)
            _add(day, "unassigned", max(0.0, house_w - rooms_w - car_w) / 1000 * hours)
            if buy is not None:
                _add(day, "house_cost", house_w / 1000 * hours * buy)
        if car_w:
            _add(day, "car", car_w / 1000 * hours)
        used = [d.get("consumed") for d in detail.values()]
        if used and all(u is not None for u in used):
            grid_in = sum(used) / 1000 * hours
            grid_out = sum(d.get("produced") or 0 for d in detail.values()) / 1000 * hours
            _add(day, "grid_in", grid_in)
            _add(day, "grid_out", grid_out)
            if buy is not None:
                _add(day, "cost_in", grid_in * buy)
            if sell is not None:
                _add(day, "earn_out", grid_out * sell)
        solar = [d.get("solar") for d in detail.values() if d.get("solar") is not None]
        if solar:
            _add(day, "solar", sum(solar) / 1000 * hours)
        if NIGHT[0] <= local.hour < NIGHT[1] and house_w is not None:
            night = self.nights.setdefault(local.strftime("%Y-%m-%d"), {"n": 0, "house": 0.0, "parts": {}, "names": {}})
            n = night["n"]
            night["house"] = round((night["house"] * n + house_w) / (n + 1), 2)
            for area, r in rooms.items():
                for p in r.get("parts") or []:
                    if p.get("watts") is None or p.get("kind") not in ("switch", "meter", "bundle"):
                        continue
                    key = f"{area}|{p['key']}"
                    old = night["parts"].get(key, 0.0)
                    night["parts"][key] = round((old * n + p["watts"]) / (n + 1), 2)
                    night["names"][key] = p.get("name") or p["key"]
            night["n"] = n + 1
        if local.minute == 0 and local.second < 31:
            cutoff = (local - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
            self.days = {k: v for k, v in self.days.items() if k >= cutoff}
            ncut = (local - timedelta(days=14)).strftime("%Y-%m-%d")
            self.nights = {k: v for k, v in self.nights.items() if k >= ncut}
        self._save()
        async_dispatcher_send(self.hass, SIGNAL_METER)

    # ── for the panel ──────────────────────────────────────────────────────

    def base_load(self) -> dict[str, Any] | None:
        """The last 7 nights: the house's average power and the parts that stay on."""
        today = dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m-%d")
        nights = [v for k, v in sorted(self.nights.items()) if v.get("n", 0) >= 20 and k <= today][-7:]
        if not nights:
            return None
        house = sum(v["house"] for v in nights) / len(nights)
        parts: dict[str, list[float]] = {}
        names: dict[str, str] = {}
        for v in nights:
            for k, w in (v.get("parts") or {}).items():
                parts.setdefault(k, []).append(w)
                names[k] = (v.get("names") or {}).get(k, k)
        avg = {k: sum(ws) / len(ws) for k, ws in parts.items()}
        known = [{"key": k, "area": k.split("|", 1)[0], "name": names[k], "watts": round(w, 1)}
                 for k, w in sorted(avg.items(), key=lambda kv: -kv[1]) if w >= 1]
        known_w = sum(p["watts"] for p in known)
        return {"watts": round(house, 1), "nights": len(nights), "parts": known[:8],
                "unassigned": round(max(0.0, house - known_w), 1)}

    def overview(self) -> dict[str, Any]:
        from .tariff import buy_now  # noqa: PLC0415

        hass = self.hass
        cfg = _cfg(hass)
        energy = hass.data.get(DOMAIN, {}).get("energy")
        status = (getattr(energy, "last_status", None) or (energy.status() if energy else {})) or {}
        detail = status.get("phase_detail") or {}
        phases = status.get("phases") or {}
        rooms = status.get("rooms") or {}
        car = status.get("car") or {}
        used = [d.get("consumed") for d in detail.values()]
        grid_w = None
        if used and all(u is not None for u in used):
            grid_w = sum(used) - sum(d.get("produced") or 0 for d in detail.values())
        solar_vals = [d.get("solar") for d in detail.values() if d.get("solar") is not None]
        house_vals = [v for v in phases.values() if v is not None]
        house_w = sum(house_vals) if house_vals and len(house_vals) == len(phases) else None
        car_w = (car.get("kw") or 0.0) * 1000 if car.get("charging") else 0.0
        rooms_w = sum((r.get("watts") or 0.0) for r in rooms.values())
        today = self.days.get(dt_util.as_local(dt_util.utcnow()).strftime("%Y-%m-%d")) or {}
        fuse = float(cfg.get("fuse_a") or DEFAULT_FUSE)
        phase_rows = []
        for p, d in detail.items():
            amps = max(d.get("consumed") or 0.0, d.get("produced") or 0.0) / VOLT
            phase_rows.append({"phase": p, "amps": round(amps, 1),
                               "rooms": [a for a, r in rooms.items() if (r.get("phase") or "L1") == p]})
        warning = None
        if car and not car.get("charging") and detail:
            cp = car.get("phase") or "L1"
            row = next((r for r in phase_rows if r["phase"] == cp), None)
            add = float(cfg.get("charger_max_kw") or 3.7) * 1000 / VOLT
            if row and row["amps"] + add > fuse:
                warning = {"phase": cp, "car_a": round(add), "total_a": round(row["amps"] + add)}
        room_rows = []
        for area, r in rooms.items():
            parts = sorted([p for p in r.get("parts") or [] if (p.get("watts") or 0) >= 1], key=lambda p: -(p.get("watts") or 0))
            room_rows.append({"area": area, "watts": r.get("watts") or 0.0,
                              "top": [{"name": p.get("name") or p["key"], "watts": p["watts"]} for p in parts[:3]],
                              "kwh": round((today.get("rooms") or {}).get(area, 0.0), 2),
                              "cost": round((today.get("rooms_cost") or {}).get(area, 0.0), 2) if today.get("rooms_cost") else None})
        room_rows.sort(key=lambda r: (-r["watts"], -r["kwh"]))
        base = self.base_load()
        price = buy_now(hass)
        if base and price is not None:
            base["month"] = round(base["watts"] / 1000 * 24 * 30 * price, 2)
        return {
            "configured": bool(status.get("configured")),
            "price": price,
            "now": {"grid_w": None if grid_w is None else round(grid_w), "solar_w": round(sum(solar_vals)) if solar_vals else None,
                    "house_w": None if house_w is None else round(house_w), "car_w": round(car_w),
                    "rooms_w": round(rooms_w), "unassigned_w": None if house_w is None else round(max(0.0, house_w - rooms_w - car_w)),
                    "car": {"charging": bool(car.get("charging")), "name": car.get("name") or None} if car else None},
            "today": {k: round(today.get(k, 0.0), 2) for k in ("house", "grid_in", "grid_out", "solar", "car", "unassigned",
                                                                  "cost_in", "earn_out", "house_cost") if k in today},
            "has_solar": bool(cfg.get("has_solar")),
            "fuse_a": fuse, "phases": phase_rows, "warning": warning,
            "rooms": room_rows, "base": base,
            "upcoming": self._upcoming(), "recent": self._recent(),
        }

    # ── the bill ───────────────────────────────────────────────────────────

    async def _gas_days(self, start: datetime, end: datetime) -> tuple[dict[str, float], bool]:
        """m³ per local day from the Energy dashboard's gas meter(s), and whether there is one."""
        try:
            from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

            manager = await async_get_manager(self.hass)
            ids = {s["stat_energy_from"] for s in (manager.data or {}).get("energy_sources") or []
                   if s.get("type") == "gas" and s.get("stat_energy_from")}
        except Exception:  # noqa: BLE001 - no Energy dashboard
            return {}, False
        if not ids:
            return {}, False
        try:
            from homeassistant.components.recorder import get_instance  # noqa: PLC0415
            from homeassistant.components.recorder.statistics import statistics_during_period  # noqa: PLC0415

            stats = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period, self.hass, start, end, ids, "hour", None, {"change"})
        except Exception:  # noqa: BLE001
            return {}, True
        out: dict[str, float] = {}
        for rows in stats.values():
            for r in rows:
                if r.get("change") is None:
                    continue
                t = dt_util.utc_from_timestamp(r["start"]) if isinstance(r["start"], (int, float)) else r["start"]
                key = dt_util.as_local(t).strftime("%Y-%m-%d")
                out[key] = round(out.get(key, 0.0) + max(0.0, r["change"]), 4)
        return out, True

    async def async_bill(self, month: str | None = None) -> dict[str, Any]:
        """One month (YYYY-MM, default this one): per day electricity, gas and
        fixed costs, the total so far, the forecast and the advance payment."""
        cfg = _cfg(self.hass).get("bill") or {}
        now = dt_util.as_local(dt_util.utcnow())
        this_month = now.strftime("%Y-%m")
        month = month or this_month
        year, mon = (int(x) for x in month.split("-"))
        days_in = calendar.monthrange(year, mon)[1]
        first = now.replace(year=year, month=mon, day=1, hour=0, minute=0, second=0, microsecond=0)
        current = month == this_month
        upto = now.day if current else days_in
        termijn = cfg.get("termijn") if isinstance(cfg.get("termijn"), (int, float)) else None
        fixed = float(cfg.get("fixed_month") or 0.0)
        gas_price = cfg.get("gas_price") if isinstance(cfg.get("gas_price"), (int, float)) else None
        gas_from = first - timedelta(days=14) if current else first
        gas, has_gas = await self._gas_days(dt_util.as_utc(gas_from), dt_util.as_utc(first + timedelta(days=days_in)))
        rows = []
        for d in range(1, days_in + 1):
            key = f"{month}-{d:02d}"
            day = self.days.get(key) or {}
            elec = None if "cost_in" not in day else round(day.get("cost_in", 0.0) - day.get("earn_out", 0.0), 3)
            m3 = gas.get(key)
            rows.append({"day": d, "elec": elec, "kwh_in": round(day.get("grid_in", 0.0), 2) if day else None,
                         "kwh_out": round(day.get("grid_out", 0.0), 2) if day else None,
                         "gas_m3": m3, "gas": None if m3 is None or gas_price is None else round(m3 * gas_price, 3),
                         "fixed": round(fixed / days_in, 3), "future": current and d > upto})
        past = [r for r in rows if not r["future"]]
        elec_so_far = round(sum(r["elec"] or 0.0 for r in past), 2)
        gas_so_far = round(sum(r["gas"] or 0.0 for r in past), 2) if gas_price is not None and has_gas else None
        fixed_so_far = round(fixed / days_in * upto, 2)
        total = round(elec_so_far + (gas_so_far or 0.0) + fixed_so_far, 2)
        measured = [k for k, v in sorted(self.days.items()) if "cost_in" in v]
        out: dict[str, Any] = {
            "month": month, "current": current, "days": days_in, "upto": upto, "rows": rows,
            "elec": elec_so_far, "gas": gas_so_far, "fixed": fixed_so_far, "total": total,
            "kwh_in": round(sum(r["kwh_in"] or 0 for r in past), 1), "kwh_out": round(sum(r["kwh_out"] or 0 for r in past), 1),
            "gas_m3": round(sum(r["gas_m3"] or 0 for r in past), 2) if has_gas else None,
            "has_gas": has_gas, "gas_price": gas_price, "termijn": termijn, "fixed_month": fixed,
            "since": measured[0] if measured else None,
            "months": sorted({k[:7] for k in self.days} | {this_month}),
        }
        if current:
            # The average day of the last 14 days (electricity + gas), for the days to come.
            last = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 15)]
            elec_days = [self.days[k].get("cost_in", 0.0) - self.days[k].get("earn_out", 0.0) for k in last if "cost_in" in self.days.get(k, {})]
            gas_days = [gas[k] * gas_price for k in last if k in gas and gas_price is not None]
            per_day = (sum(elec_days) / len(elec_days) if elec_days else 0.0) + (sum(gas_days) / len(gas_days) if gas_days else 0.0)
            left = days_in - upto
            # today is only partly gone: count what is left of it too
            frac = 1 - (now.hour * 60 + now.minute) / 1440
            out["forecast"] = round(total + per_day * (left + frac) + fixed / days_in * left, 2) if elec_days else None
            out["per_day"] = round(per_day, 2) if elec_days else None
            if out["forecast"] is not None and termijn is not None:
                out["diff"] = round(out["forecast"] - termijn, 2)
        elif termijn is not None:
            out["diff"] = round(total - termijn, 2)
        return out

    def _upcoming(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        now = dt_util.utcnow()
        planner = self.hass.data.get(DOMAIN, {}).get("planner")
        for plan in (getattr(planner, "plans", None) or {}).values():
            block = plan.get("block")
            if not block or plan.get("done") or plan.get("mode_used") == "direct":
                continue
            start = dt_util.parse_datetime(block["start"])
            if start is None or start < now - timedelta(hours=1):
                continue
            dev = plan.get("device") or {}
            out.append({"at": block["start"], "end": block["end"], "kind": "plan", "device": dev.get("kind"),
                        "name": dev.get("name"), "mode": plan.get("mode_used"), "price": block.get("avg"),
                        "ready": plan.get("ready")})
        battery = self.hass.data.get(DOMAIN, {}).get("battery")
        if battery is not None and getattr(battery, "plan", None):
            for b in battery.blocks():
                if b["action"] in ("charge", "discharge") and dt_util.parse_datetime(b["end"]) > now:
                    out.append({"at": b["start"], "end": b["end"], "kind": "battery", "action": b["action"], "price": b.get("price")})
        out.sort(key=lambda x: x["at"])
        return out[:6]

    def _recent(self) -> list[dict[str, Any]]:
        entities = self.hass.data.get(DOMAIN, {}).get("entities", {})
        rows = []
        for area, light in entities.items():
            buf = getattr(light, "_debug", None)
            for e in (list(getattr(buf, "entries", []) or [])[-40:]):
                if e.get("kind") in ("on", "off") and (e.get("reason", "").startswith(("plan_", "switches_")) or e.get("reason") in (
                        "nobody_home", "alarm armed away", "replay", "usage_schedule")):
                    rows.append({**{k: e.get(k) for k in ("at", "kind", "reason", "bundles")}, "area": area})
        rows.sort(key=lambda r: r["at"], reverse=True)
        return rows[:6]
