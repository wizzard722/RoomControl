"""Nord Pool market prices for the energy contract (tariff.py).

Two integrations give Nord Pool prices:
- the custom one from HACS: today's and tomorrow's prices are in the
  sensor's attributes ("raw_today" / "raw_tomorrow"), read like any other
  price sensor (ev.price_forecast);
- the one built into Home Assistant: its "current price" sensor (unique id
  "<area>-current_price") only has the price now; the prices per period
  come from the action nordpool.get_prices_for_date (in currency per MWh).
  NordPoolPrices fetches today and tomorrow with it, every half hour while
  they are missing or older than an hour, and keeps them here.

find_sensor() picks a Nord Pool price sensor by itself, for the market price
"automatic" when the price sensor has no price without tax.
"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_CONFIG_UPDATED

_LOGGER = logging.getLogger(__name__)

REFRESH = timedelta(hours=1)


def _entry(hass: HomeAssistant, sensor: str | None) -> er.RegistryEntry | None:
    return er.async_get(hass).async_get(sensor) if sensor else None


def is_builtin(hass: HomeAssistant, sensor: str | None) -> bool:
    """The built-in integration's current price sensor (no prices in its attributes)."""
    entry = _entry(hass, sensor)
    st = hass.states.get(sensor or "")
    return bool(
        entry is not None and entry.platform == "nordpool" and str(entry.unique_id).endswith("-current_price")
        and not (st is not None and isinstance(st.attributes.get("raw_today"), list))
    )


def services(hass: HomeAssistant) -> list[dict[str, str]]:
    """The Nord Pool services (config entries) of this Home Assistant: [{"id", "title"}]."""
    try:
        return [{"id": e.entry_id, "title": e.title or "Nord Pool"} for e in hass.config_entries.async_entries("nordpool")]
    except Exception:  # noqa: BLE001
        return []


def find_sensor(hass: HomeAssistant, entry_id: str | None = None) -> str | None:
    """The price sensor of a Nord Pool service (config entry; None: any): the
    HACS one (prices in its attributes) first, else the built-in current
    price sensor. The user picks the service, RoomControl its sensor."""
    found: list[tuple[int, str]] = []
    try:
        entries = list(er.async_get(hass).entities.values())
    except Exception:  # noqa: BLE001 - registry not loaded
        return None
    for entry in entries:
        if entry.platform != "nordpool" or entry.domain != "sensor" or entry.disabled_by:
            continue
        if entry_id and entry.config_entry_id != entry_id:
            continue
        st = hass.states.get(entry.entity_id)
        if st is not None and isinstance(st.attributes.get("raw_today"), list):
            found.append((0, entry.entity_id))
        elif str(entry.unique_id).endswith("-current_price"):
            found.append((1, entry.entity_id))
    return sorted(found)[0][1] if found else None


def cached_rows(hass: HomeAssistant, sensor: str | None) -> list[dict[str, Any]]:
    """The prices fetched for the built-in sensor: [{"start", "end", "price" €/kWh}]."""
    cache = hass.data.get(DOMAIN, {}).get("nordpool_cache", {}).get(sensor or "")
    return list(cache["rows"]) if cache else []


class NordPoolPrices:
    """Fetches the built-in Nord Pool integration's prices per period."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsubs: list[CALLBACK_TYPE] = []
        self._busy = False

    @callback
    def start(self) -> None:
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, timedelta(minutes=30)))
        self._unsubs.append(async_dispatcher_connect(self.hass, SIGNAL_CONFIG_UPDATED, self._tick))
        self._tick()

    @callback
    def shutdown(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs = []

    def _sensor(self) -> str | None:
        """The Nord Pool sensor the energy contract uses now, if it is the built-in one."""
        from .tariff import market_sensor  # noqa: PLC0415

        sensor = market_sensor(self.hass)
        return sensor if is_builtin(self.hass, sensor) else None

    @callback
    def _tick(self, *_: Any) -> None:
        sensor = self._sensor()
        if sensor is None or self._busy:
            return
        cache = self.hass.data.get(DOMAIN, {}).get("nordpool_cache", {}).get(sensor)
        now = dt_util.utcnow()
        tomorrow = dt_util.as_local(now).date() + timedelta(days=1)
        has_tomorrow = bool(cache) and any(dt_util.as_local(r["start"]).date() == tomorrow for r in cache["rows"])
        if cache and now - cache["at"] < REFRESH and (has_tomorrow or dt_util.as_local(now).hour < 13):
            return
        self._busy = True
        self.hass.async_create_task(self._async_fetch(sensor))

    async def _async_fetch(self, sensor: str) -> None:
        try:
            entry = _entry(self.hass, sensor)
            if entry is None or not entry.config_entry_id:
                return
            area = str(entry.unique_id).split("-")[0]
            today = dt_util.as_local(dt_util.utcnow()).date()
            rows: list[dict[str, Any]] = []
            for day in (today, today + timedelta(days=1)):
                try:
                    response = await self.hass.services.async_call(
                        "nordpool", "get_prices_for_date",
                        {"config_entry": entry.config_entry_id, "date": day.isoformat(), "areas": [area]},
                        blocking=True, return_response=True,
                    )
                except Exception as err:  # noqa: BLE001 - tomorrow not published yet, or offline
                    _LOGGER.debug("Nord Pool prices for %s not fetched: %s", day, err)
                    continue
                for row in (response or {}).get(area) or []:
                    start = dt_util.parse_datetime(str(row.get("start")))
                    end = dt_util.parse_datetime(str(row.get("end")))
                    price = row.get("price")
                    if start is None or end is None or not isinstance(price, (int, float)):
                        continue
                    rows.append({"start": dt_util.as_utc(start), "end": dt_util.as_utc(end),
                                 "price": float(price) / 1000})  # per MWh → per kWh
            if rows:
                rows.sort(key=lambda r: r["start"])
                self.hass.data.setdefault(DOMAIN, {}).setdefault("nordpool_cache", {})[sensor] = {
                    "rows": rows, "at": dt_util.utcnow()}
        finally:
            self._busy = False
