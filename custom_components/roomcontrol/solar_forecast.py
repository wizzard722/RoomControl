"""Expected solar power, from Home Assistant's solar forecast integrations.

Every integration that gives the Energy dashboard a solar forecast
(Forecast.Solar, Solcast, Open-Meteo Solar Forecast, …) offers it the same
way: an "energy" platform with async_get_solar_forecast(hass, entry id),
returning {"wh_hours": {iso start: Wh in that period}}.

Inside the general setting "energy":
 "solar_forecast": [config entry ids],  # chosen forecasts, added up (e.g. two roofs)
 "base_load_w": 400                     # the house's own use while the sun shines

RoomControl reads the chosen forecasts every 15 minutes. While the panels
are expected to give more than the house's own use, that surplus charges
the car for free: the cheapest time to charge counts a price block as
cheaper by the share of the charger's power the sun is expected to give.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DEFAULT_BASE_LOAD_W = 400


async def _platforms(hass: HomeAssistant) -> dict[str, Any]:
    """{domain: async_get_solar_forecast} of the loaded integrations that have one."""
    try:
        from homeassistant.components.energy.websocket_api import async_get_energy_platforms  # noqa: PLC0415

        return await async_get_energy_platforms(hass)
    except Exception:  # noqa: BLE001 - no energy integration: look ourselves
        pass
    out: dict[str, Any] = {}
    for domain in {e.domain for e in hass.config_entries.async_entries()}:
        try:
            integration = await async_get_integration(hass, domain)
            platform = await integration.async_get_platform("energy")
        except Exception:  # noqa: BLE001 - most integrations have no energy platform
            continue
        if hasattr(platform, "async_get_solar_forecast"):
            out[domain] = platform.async_get_solar_forecast
    return out


async def async_list(hass: HomeAssistant) -> list[dict[str, str]]:
    """The solar forecasts this Home Assistant has: [{"id", "title", "domain"}]."""
    platforms = await _platforms(hass)
    out = []
    for domain in sorted(platforms):
        for entry in hass.config_entries.async_entries(domain):
            out.append({"id": entry.entry_id, "title": entry.title or domain, "domain": domain})
    return out


async def async_read(hass: HomeAssistant, entry_ids: list[str]) -> dict[datetime, float]:
    """The chosen forecasts added up: {utc period start: Wh}."""
    platforms = await _platforms(hass)
    total: dict[datetime, float] = {}
    for entry_id in entry_ids:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain not in platforms:
            continue
        try:
            data = await platforms[entry.domain](hass, entry_id)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Solar forecast %s failed: %s", entry.title, err)
            continue
        for start, wh in ((data or {}).get("wh_hours") or {}).items():
            when = dt_util.parse_datetime(start) if isinstance(start, str) else start
            if when is None or not isinstance(wh, (int, float)):
                continue
            when = dt_util.as_utc(when)
            total[when] = total.get(when, 0.0) + float(wh)
    return dict(sorted(total.items()))


def periods(wh: dict[datetime, float]) -> list[dict[str, Any]]:
    """[{"start", "end", "kw"}]: each period's average power."""
    keys = list(wh)
    out = []
    for i, start in enumerate(keys):
        end = keys[i + 1] if i + 1 < len(keys) and keys[i + 1] - start <= timedelta(hours=1) else start + timedelta(hours=1)
        hours = max((end - start).total_seconds() / 3600, 1 / 60)
        out.append({"start": start, "end": end, "kw": wh[start] / 1000 / hours})
    return out


def sun_kw_at(sun: list[dict[str, Any]], start: datetime, end: datetime) -> float:
    """Average expected solar power (kW) over [start, end)."""
    span = (end - start).total_seconds()
    if span <= 0:
        return 0.0
    got = 0.0
    for p in sun:
        overlap = (min(end, p["end"]) - max(start, p["start"])).total_seconds()
        if overlap > 0:
            got += p["kw"] * overlap
    return got / span


def grid_share(sun_kw: float, base_kw: float, charger_kw: float) -> float:
    """The share of the charger's power that has to come from the grid."""
    if charger_kw <= 0:
        return 1.0
    surplus = max(0.0, sun_kw - base_kw)
    return min(1.0, max(0.0, 1 - surplus / charger_kw))
