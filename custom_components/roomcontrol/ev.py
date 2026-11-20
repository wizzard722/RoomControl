"""The car: messages about charging, and the cheapest time to charge.

Inside the general setting "energy":
 "notify": {
   "events": {"started" | "stopped" | "full" | "cheap":
              {"on": bool, "text": str}},          # empty text: the default
   "speak": bool, "speak_rooms": [area ids],      # [] = every room with speakers
   "ha": bool,                                    # a melding in Home Assistant
   "phone": bool, "persons": [person entities]},  # their phone ([] = everyone)
 "price_sensor": sensor,          # a dynamic tariff with a forecast (e.g. Zonneplan)
 "ready_by": "07:00"              # optional: the car must be charged by then

Texts may hold {name}, {kw}, {kwh} (charged this time), {cost} (its cost),
{soc}, {start}, {end} and {price}.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .announce import async_announce
from .const import DOMAIN
from .nspanel import nspanel_message
from .person_notify import person_notify_service

_LOGGER = logging.getLogger(__name__)

EVENTS = ("started", "stopped", "full", "cheap")
FULL_SOC = 98

_DEFAULTS = {
    "nl": {
        "started": ("{name} is begonnen met laden ({kw}).", True),
        "stopped": ("{name} is gestopt met laden. Er is {kwh} geladen.", True),
        "full": ("{name} is vol geladen.", True),
        "cheap": ("De goedkoopste tijd om {name} te laden begint nu ({start}–{end}, {price}).", False),
        "car": "De auto",
        "title": "Auto laden",
    },
    "en": {
        "started": ("{name} started charging ({kw}).", True),
        "stopped": ("{name} stopped charging. {kwh} was charged.", True),
        "full": ("{name} is fully charged.", True),
        "cheap": ("The cheapest time to charge {name} starts now ({start}–{end}, {price}).", False),
        "car": "The car",
        "title": "Car charging",
    },
}


def _lang(hass: HomeAssistant) -> str:
    return "nl" if (hass.config.language or "").lower().startswith("nl") else "en"


def event_defaults(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    d = _DEFAULTS[_lang(hass)]
    return {e: {"text": d[e][0], "on": d[e][1]} for e in EVENTS}


def notify_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    n = cfg.get("notify")
    return n if isinstance(n, dict) else {}


def event_cfg(hass: HomeAssistant, cfg: dict[str, Any], event: str) -> dict[str, Any]:
    """One event's settings: on/off and its text (the default when empty)."""
    default = event_defaults(hass)[event]
    own = (notify_cfg(cfg).get("events") or {}).get(event) or {}
    return {
        "on": own["on"] if isinstance(own.get("on"), bool) else default["on"],
        "text": (own.get("text") or "").strip() or default["text"],
    }


# ── prices ─────────────────────────────────────────────────────────────────

_TIME_KEYS = ("datetime", "start", "start_time", "from", "time", "timestamp", "date")
_PRICE_KEYS = ("electricity_price", "price", "value", "total", "price_incl", "tariff")


def _when(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return dt_util.as_utc(value)
    if isinstance(value, (int, float)):
        return dt_util.utc_from_timestamp(value / 1000 if value > 1e11 else value)
    if isinstance(value, str):
        parsed = dt_util.parse_datetime(value)
        return dt_util.as_utc(parsed) if parsed else None
    return None


def _rows(attrs: dict[str, Any]) -> list[dict[str, Any]]:
    """Every list of {time, price} rows in the sensor's attributes."""
    rows: list[dict[str, Any]] = []
    for key, value in attrs.items():
        if not isinstance(value, list) or not value or not isinstance(value[0], dict):
            continue
        if key in ("raw_today", "raw_tomorrow", "forecast", "prices", "prices_today", "prices_tomorrow", "data") or any(
            k in value[0] for k in _TIME_KEYS
        ):
            rows.extend(r for r in value if isinstance(r, dict))
    return rows


def price_forecast(hass: HomeAssistant, sensor: str | None) -> list[dict[str, Any]]:
    """[{"start": utc datetime, "end": utc datetime, "price": €/kWh}], sorted.
    Reads the forecast in the price sensor's attributes: Zonneplan
    ("forecast": [{"datetime", "electricity_price"}], in 1/10,000,000 €),
    Nord Pool ("raw_today"/"raw_tomorrow": [{"start", "end", "value"}]),
    ENTSO-e / EnergyZero ("prices": [{"time", "price"}]) and alike."""
    st = hass.states.get(sensor or "")
    if st is None:
        return []
    out: list[dict[str, Any]] = []
    for row in _rows(dict(st.attributes)):
        start = next((t for k in _TIME_KEYS if (t := _when(row.get(k))) is not None), None)
        price = next((row[k] for k in _PRICE_KEYS if isinstance(row.get(k), (int, float))), None)
        if start is None or price is None:
            continue
        end = _when(row.get("end")) or _when(row.get("end_time")) or _when(row.get("till"))
        out.append({"start": start, "end": end, "price": float(price)})
    if not out:
        return []
    out.sort(key=lambda r: r["start"])
    # One row per start time.
    seen: dict[datetime, dict[str, Any]] = {}
    for r in out:
        seen[r["start"]] = r
    out = list(seen.values())
    biggest = max(abs(r["price"]) for r in out)
    scale = 1e7 if biggest > 1000 else 100 if biggest > 5 else 1  # Zonneplan: 1e-7 €; ct/kWh
    for i, r in enumerate(out):
        r["price"] = r["price"] / scale
        if r["end"] is None:
            nxt = out[i + 1]["start"] if i + 1 < len(out) else None
            r["end"] = nxt if nxt and nxt - r["start"] <= timedelta(hours=1) else r["start"] + timedelta(hours=1)
    return out


def price_now(hass: HomeAssistant, sensor: str | None, rows: list[dict[str, Any]]) -> float | None:
    now = dt_util.utcnow()
    for r in rows:
        if r["start"] <= now < r["end"]:
            return round(r["price"], 4)
    st = hass.states.get(sensor or "")
    try:
        value = float(st.state) if st is not None else None
    except (TypeError, ValueError):
        return None
    if value is None:
        return None
    return value / 1e7 if abs(value) > 1000 else value / 100 if abs(value) > 5 else value


def _ready_by(value: Any, now: datetime) -> datetime | None:
    """The next moment at this local time (HH:MM)."""
    if not isinstance(value, str) or ":" not in value:
        return None
    try:
        h, m = (int(x) for x in value.split(":")[:2])
    except ValueError:
        return None
    local = dt_util.as_local(now)
    at = local.replace(hour=h, minute=m, second=0, microsecond=0)
    if at <= local:
        at += timedelta(days=1)
    return dt_util.as_utc(at)


def cheapest(rows: list[dict[str, Any]], hours: float, now: datetime | None = None,
             ready_by: datetime | None = None) -> dict[str, Any] | None:
    """The cheapest unbroken stretch of `hours` from now (the current slot
    counts for what is left of it), ending by `ready_by` when given.
    Returns {"start", "end", "avg"} (utc datetimes, €/kWh) or None."""
    now = now or dt_util.utcnow()
    rows = [r for r in rows if r["end"] > now and (ready_by is None or r["start"] < ready_by)]
    if not rows or hours <= 0:
        return None
    need = timedelta(hours=hours)

    def cost_of(start: datetime) -> float | None:
        """Average price from `start` for `need`, or None (a gap / past the end)."""
        end, got, cost, at = start + need, timedelta(0), 0.0, start
        if ready_by is not None and end > ready_by + timedelta(seconds=1):
            return None
        for r in rows:
            if r["end"] <= at or got >= need:
                continue
            if r["start"] > at + timedelta(minutes=1):
                return None  # a gap in the forecast
            take = min(r["end"], end) - max(r["start"], at)
            cost += r["price"] * take.total_seconds()
            got += take
            at = max(r["start"], at) + take
        return cost / need.total_seconds() if got >= need - timedelta(seconds=1) else None

    # The best stretch starts at the start of a slot (or now) or ends at the end of one.
    starts = sorted({max(now, r["start"]) for r in rows} | {r["end"] - need for r in rows if r["end"] - need >= now})
    best: dict[str, Any] | None = None
    for start in starts:
        avg = cost_of(start)
        if avg is not None and (best is None or avg < best["avg"] - 1e-9):
            best = {"start": start, "end": start + need, "avg": avg}
    return best


def charge_hours(cfg: dict[str, Any], soc: float | None, battery_kwh: float, max_kw: float) -> float:
    """Hours needed to charge to full at the charger's maximum."""
    if max_kw <= 0:
        return 0.0
    need = battery_kwh * (1 - (soc if soc is not None else 0) / 100)
    return max(0.0, need / max_kw)


def price_status(hass: HomeAssistant, cfg: dict[str, Any], car: dict[str, Any]) -> dict[str, Any] | None:
    """For the panel: the forecast and the cheapest time to charge."""
    sensor = cfg.get("price_sensor")
    if not sensor:
        return None
    rows = price_forecast(hass, sensor)
    now = dt_util.utcnow()
    max_kw = float(cfg.get("charger_max_kw") or 3.7)
    battery = float(car.get("battery_kwh") or 8.8)
    hours = charge_hours(cfg, car.get("soc"), battery, max_kw)
    need_kwh = hours * max_kw  # all the energy this charge needs, to full
    ready = _ready_by(cfg.get("ready_by"), now)
    best = cheapest(rows, hours, now, ready) if hours > 0 else None
    upcoming = [r for r in rows if r["end"] > now][:48]
    return {
        "sensor": sensor,
        "now": price_now(hass, sensor, rows),
        "hours": round(hours, 2),
        "kwh": round(need_kwh, 2),
        "soc_known": car.get("soc") is not None,
        "ready_by": ready.isoformat() if ready else None,
        "cheapest": None if best is None else {
            "start": best["start"].isoformat(), "end": best["end"].isoformat(), "avg": round(best["avg"], 4),
            "cost": round(best["avg"] * need_kwh, 2),
            "cost_now": None if (p := price_now(hass, sensor, rows)) is None else round(p * need_kwh, 2)},
        "forecast": [{"start": r["start"].isoformat(), "end": r["end"].isoformat(), "price": round(r["price"], 4)}
                     for r in upcoming],
        "found": bool(rows),
    }


# ── messages ───────────────────────────────────────────────────────────────

def _fmt_kw(value: Any, lang: str) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    s = f"{v:.1f}"
    return (s.replace(".", ",") if lang == "nl" else s) + " kW"


def _fmt_kwh(value: Any, lang: str) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:.1f}"
    return (s.replace(".", ",") if lang == "nl" else s) + " kWh"


def _fmt_time(value: Any) -> str:
    when = _when(value)
    return dt_util.as_local(when).strftime("%H:%M") if when else "—"


def _fmt_price(value: Any, lang: str) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    s = f"{v:.2f}"
    return "€ " + (s.replace(".", ",") if lang == "nl" else s) + "/kWh"


def render(hass: HomeAssistant, text: str, car: dict[str, Any], price: dict[str, Any] | None = None) -> str:
    lang = _lang(hass)
    best = (price or {}).get("cheapest") or {}
    values = {
        "name": (car.get("name") or "").strip() or _DEFAULTS[lang]["car"],
        "kw": _fmt_kw(car.get("kw"), lang),
        "kwh": _fmt_kwh(car.get("charged_kwh"), lang),
        "soc": "—" if car.get("soc") is None else f"{round(car['soc'])}%",
        "start": _fmt_time(best.get("start")),
        "end": _fmt_time(best.get("end")),
        "price": _fmt_price(best.get("avg"), lang),
        "cost": "—" if car.get("cost") is None else "€ " + (f"{float(car['cost']):.2f}".replace(".", ",") if lang == "nl" else f"{float(car['cost']):.2f}"),
    }
    out = text
    for key, value in values.items():
        out = out.replace("{" + key + "}", value)
    return out[:1].upper() + out[1:]


async def async_send(hass: HomeAssistant, cfg: dict[str, Any], message: str, test: bool = False) -> dict[str, Any]:
    """Send one message on the chosen channels. Returns where it went."""
    n = notify_cfg(cfg)
    title = _DEFAULTS[_lang(hass)]["title"] + (" (test)" if test else "")
    result: dict[str, Any] = {"players": [], "services": [], "ha": False, "no_device": []}
    persons = [p for p in n.get("persons") or [] if p]
    if n.get("phone") and not persons:
        persons = list(hass.data.get(DOMAIN, {}).get("settings", {}).get("persons") or [])
    for person in persons if n.get("phone") else []:
        service = person_notify_service(hass, person)
        if not service:
            st = hass.states.get(person)
            result["no_device"].append(st.attributes.get("friendly_name", person) if st else person)
        elif service not in result["services"]:
            result["services"].append(service)
    for service in result["services"]:
        try:
            await hass.services.async_call(
                "notify", service.split(".", 1)[1], {"title": title, "message": message}, blocking=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("EV message to %s failed: %s", service, err)
    if not test:
        nspanel_message(hass, "ev", message, target=n.get("nspanel"))
    if n.get("ha", True):
        persistent_notification.async_create(hass, message, title=title, notification_id=f"{DOMAIN}_ev")
        result["ha"] = True
    if n.get("speak"):
        rooms = [r for r in n.get("speak_rooms") or [] if r]
        result["players"] = await async_announce(hass, message, rooms or None, kind="ev")
    return result


class EvNotifier:
    """Watches the car's charging state (each energy check) and sends the
    chosen messages. A change counts once it held for two checks (a minute),
    so a short dip in the estimate gives no message."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._state: bool | None = None  # the charging state last told
        self._seen: bool | None = None
        self._seen_count = 0
        self._last_car: dict[str, Any] = {}
        self._cheap_told: str | None = None

    @callback
    def update(self, cfg: dict[str, Any], car: dict[str, Any] | None, price: dict[str, Any] | None) -> None:
        if not car:
            return
        charging = bool(car.get("charging"))
        if charging == self._seen:
            self._seen_count += 1
        else:
            self._seen, self._seen_count = charging, 1
        if self._state is None:
            self._state = charging  # start-up: no message for the state it found
        elif self._seen_count >= 2 and charging != self._state:
            self._state = charging
            if charging:
                self._fire(cfg, "started", car, price)
            else:
                last = self._last_car or car
                soc = car.get("soc") if car.get("soc") is not None else last.get("soc")
                ended = {**car, "charged_kwh": last.get("charged_kwh"), "kw": last.get("kw"), "cost": last.get("cost")}
                self._fire(cfg, "full" if soc is not None and soc >= FULL_SOC else "stopped", ended, price)
        if charging:
            self._last_car = dict(car)
        self._check_cheap(cfg, car, price)

    @callback
    def _check_cheap(self, cfg: dict[str, Any], car: dict[str, Any], price: dict[str, Any] | None) -> None:
        best = (price or {}).get("cheapest")
        if not best or car.get("charging") or car.get("plugged") is False:
            return
        if car.get("soc") is not None and car["soc"] >= FULL_SOC:
            return
        start = _when(best["start"])
        now = dt_util.utcnow()
        if start is None or not (start <= now < start + timedelta(minutes=5)) or self._cheap_told == best["start"]:
            return
        self._cheap_told = best["start"]
        self._fire(cfg, "cheap", car, price)

    @callback
    def _fire(self, cfg: dict[str, Any], event: str, car: dict[str, Any], price: dict[str, Any] | None) -> None:
        ev = event_cfg(self.hass, cfg, event)
        if not ev["on"]:
            return
        message = render(self.hass, ev["text"], car, price)
        _LOGGER.debug("EV message (%s): %s", event, message)
        self.hass.async_create_task(async_send(self.hass, cfg, message))

    async def async_test(self, cfg: dict[str, Any], event: str, car: dict[str, Any] | None,
                         price: dict[str, Any] | None) -> dict[str, Any]:
        ev = event_cfg(self.hass, cfg, event)
        sample = dict(car or {})
        for key, value in (("kw", 3.6), ("charged_kwh", 6.4), ("soc", 80), ("cost", 1.28)):
            if not sample.get(key):
                sample[key] = value
        message = render(self.hass, ev["text"], sample, price)
        return {"message": message, **(await async_send(self.hass, cfg, message, test=True))}
