"""Time slots ("tijdvakken"), shared by bundles with own times and locks.

A slot: {"days": [0..6] (Monday = 0), "start": {"type": "time", "time":
"HH:MM"} | {"type": "dusk"} | {"type": "dark"}, "end": {"type": "time",
"time": "HH:MM"} | {"type": "sunrise"}, "holiday": "normal" | "vacation"}.
A slot that ends before it starts (or at sunrise) runs past midnight into
the next day.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def hm_minutes(value: Any) -> int | None:
    """"HH:MM" → minutes after midnight (None when invalid)."""
    try:
        h, m = (int(x) for x in str(value).split(":")[:2])
    except ValueError:
        return None
    return h * 60 + m if 0 <= h < 24 and 0 <= m < 60 else None


def slot_part(slot: dict[str, Any], now: datetime, phase: str, sun_down: bool) -> str | None:
    """"today" (the slot started today), "carry" (yesterday's slot running
    past midnight) or None (not running). `phase`: "light", "dusk" or "dark"."""
    days = {d for d in slot.get("days", []) or [] if isinstance(d, int)}
    start, end = slot.get("start") or {}, slot.get("end") or {}
    t = now.hour * 60 + now.minute
    today, yesterday = now.weekday(), (now.weekday() - 1) % 7
    s_type, e_type = start.get("type", "time"), end.get("type", "time")
    if s_type == "time":
        s_min = hm_minutes(start.get("time"))
        if s_min is None:
            return None
        started = t >= s_min
    else:  # schemer / donker: only counts in the afternoon/evening
        s_min = 12 * 60
        started = t >= s_min and (phase in ("dusk", "dark") if s_type == "dusk" else phase == "dark")
    if e_type == "sunrise":
        crosses, e_min = True, None
    else:
        e_min = hm_minutes(end.get("time"))
        if e_min is None:
            return None
        crosses = e_min <= s_min if s_type == "time" else e_min < 12 * 60
    if today in days and started and (crosses or t < e_min):
        return "today"
    if yesterday in days and crosses:  # yesterday's slot running into today
        if e_type == "sunrise":
            return "carry" if t < 12 * 60 and sun_down else None
        return "carry" if t < e_min else None
    return None


def mode_slots(slots: list[Any], vacation: bool) -> list[dict[str, Any]]:
    """The slots that count now: normal ones; during vacation the vacation
    slots — or, when there are none, the normal ones."""
    slots = [s for s in slots or [] if isinstance(s, dict)]
    is_vacation = lambda s: s.get("holiday") in ("vacation", "only")  # noqa: E731 ("only": older)
    normal = [s for s in slots if not is_vacation(s)]
    if vacation:
        return [s for s in slots if is_vacation(s)] or normal
    return normal
