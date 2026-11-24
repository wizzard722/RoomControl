"""The energy contract: what a kWh costs to buy and what it brings when fed in.

Inside the general setting "energy":
 "price_sensor": sensor,     # dynamic contract: the price you pay (with forecast,
                             # e.g. Zonneplan per quarter hour), including tax and markup
 "price_kwh": 0.25,          # fixed contract (no price sensor)
 "market_source": "auto" | "sensor" | "derived" | "fixed",
 "market_sensor": sensor,    # "sensor": the bare market price (e.g. Nord Pool)
 "energy_tax_kwh": 0.1088,   # "derived": energy tax per kWh, without VAT
 "buy_markup_kwh": 0.02,     # "derived": the supplier's markup per kWh, without VAT
 "feed_in_kwh": 0.05,        # "fixed": what a fed-in kWh brings
 "feed_in_cost_kwh": 0.0     # subtracted from what a fed-in kWh brings (0: none)

With a dynamic contract a fed-in kWh brings the bare market price (no energy
tax, no VAT), which can be negative. Where that price comes from:
 - "auto": the price sensor's own price without tax when it has one (e.g.
   Zonneplan's "price_tax_excluded"), else a market price sensor when one
   is chosen, else derived;
 - "sensor": the chosen market price sensor (e.g. Nord Pool, ENTSO-e);
 - "derived": price you pay ÷ 1.21 − energy tax − markup (an approximation);
 - "fixed": a fixed amount per kWh (fixed contracts).

Everything that needs a price (the car, planning, the home battery, the
"does switching off pay" analysis) asks this module.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN

VAT = 1.21
MARKET_SOURCES = ("auto", "sensor", "derived", "fixed")


def _cfg(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.get(DOMAIN, {}).get("settings", {}).get("energy") or {}


def _num(value: Any, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else default


def buy_rows(hass: HomeAssistant) -> list[dict[str, Any]]:
    """[{"start", "end", "price"}] of the price you pay (empty: fixed contract or no forecast)."""
    from .ev import price_forecast  # noqa: PLC0415

    return price_forecast(hass, _cfg(hass).get("price_sensor"))


def buy_now(hass: HomeAssistant) -> float | None:
    """The price you pay now (€/kWh): the price sensor, else the fixed price."""
    from .ev import price_now  # noqa: PLC0415

    cfg = _cfg(hass)
    if sensor := cfg.get("price_sensor"):
        if (price := price_now(hass, sensor, buy_rows(hass))) is not None:
            return price
    value = cfg.get("price_kwh")
    return float(value) if isinstance(value, (int, float)) else None


def _derive(price: float, cfg: dict[str, Any]) -> float:
    return price / VAT - _num(cfg.get("energy_tax_kwh")) - _num(cfg.get("buy_markup_kwh"))


def market_rows(hass: HomeAssistant) -> tuple[list[dict[str, Any]], str | None]:
    """The bare market price per period and where it came from:
    "price_sensor" (its price without tax), "market_sensor", "derived",
    "fixed" or None (nothing to go on)."""
    from .ev import price_forecast  # noqa: PLC0415

    cfg = _cfg(hass)
    source = cfg.get("market_source") if cfg.get("market_source") in MARKET_SOURCES else "auto"
    if source == "fixed":
        return [], "fixed"
    if source == "auto" and cfg.get("price_sensor"):
        if rows := price_forecast(hass, cfg["price_sensor"], market=True):
            return rows, "price_sensor"
    if source in ("auto", "sensor") and cfg.get("market_sensor"):
        if rows := price_forecast(hass, cfg["market_sensor"]):
            return rows, "market_sensor"
    if rows := buy_rows(hass):
        return [{**r, "price": _derive(r["price"], cfg)} for r in rows], "derived"
    if cfg.get("price_sensor") or isinstance(cfg.get("price_kwh"), (int, float)):
        return [], "derived"
    return [], None


def _at(rows: list[dict[str, Any]], when: datetime) -> float | None:
    for r in rows:
        if r["start"] <= when < r["end"]:
            return r["price"]
    return None


def sell_at(hass: HomeAssistant, when: datetime | None = None,
            rows: tuple[list[dict[str, Any]], str | None] | None = None) -> float | None:
    """What one fed-in kWh brings at that moment (€; negative: it costs)."""
    cfg = _cfg(hass)
    when = when or dt_util.utcnow()
    market, source = rows if rows is not None else market_rows(hass)
    cost = _num(cfg.get("feed_in_cost_kwh"))
    if source == "fixed":
        return _num(cfg.get("feed_in_kwh")) - cost
    price = _at(market, when)
    if price is None and source == "derived" and (buy := buy_now(hass)) is not None and when - dt_util.utcnow() < timedelta(minutes=1):
        price = _derive(buy, cfg)
    return None if price is None else price - cost


def sell_now(hass: HomeAssistant) -> float | None:
    return sell_at(hass)


def forecast(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Per period from now on: {"start", "end", "buy", "sell"} (€/kWh)."""
    now = dt_util.utcnow()
    market = market_rows(hass)
    out = []
    for r in buy_rows(hass):
        if r["end"] <= now:
            continue
        out.append({"start": r["start"], "end": r["end"], "buy": round(r["price"], 4),
                    "sell": None if (s := sell_at(hass, r["start"], market)) is None else round(s, 4)})
    return out


def status(hass: HomeAssistant) -> dict[str, Any]:
    """For the panel: the prices now and where they come from."""
    cfg = _cfg(hass)
    market, source = market_rows(hass)
    buy = buy_now(hass)
    sell = sell_at(hass, rows=(market, source))
    rows = buy_rows(hass)
    return {
        "buy": None if buy is None else round(buy, 4),
        "buy_source": "sensor" if cfg.get("price_sensor") and buy is not None and rows else
                      "sensor_now" if cfg.get("price_sensor") and buy is not None else
                      "fixed" if isinstance(cfg.get("price_kwh"), (int, float)) else None,
        "market": None if (m := _at(market, dt_util.utcnow())) is None else round(m, 4),
        "market_source": source,
        "sell": None if sell is None else round(sell, 4),
        "periods": len(rows),
        "until": rows[-1]["end"].isoformat() if rows else None,
    }
