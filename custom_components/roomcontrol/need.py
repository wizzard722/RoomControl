"""When is a planned device needed? RoomControl predicts the "ready by" time.

Per day the first quarter of an hour the device was in use counts as the
moment it was needed: from device learning "use" (for a device that keeps
warm only real use, "big"), leaving out the stretches RoomControl itself
switched it on for (planning), plus the moments the user switched it on by
hand while planning held it off (and, for the car, when it was unplugged).

Per weekday the need is the earlier quarter of those moments (the lower
quartile, so it is ready on most days): from MIN_SAME days of that weekday,
else from the weekdays or the weekend together, else from all days (MIN_POOL
moments). Too few moments: the default (07:00) and "learning".
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

Q = 96
MIN_SAME = 2
MIN_POOL = 3
KEEP_DAYS = 42
DEFAULT_Q = 28  # 07:00


def _local(iso: str) -> datetime | None:
    t = dt_util.parse_datetime(iso) if isinstance(iso, str) else None
    return dt_util.as_local(t) if t is not None else None


def _own(blocks: list[Any]) -> set[tuple[str, int]]:
    """(local day, quarter) covered by RoomControl's own stretches."""
    out: set[tuple[str, int]] = set()
    for b in blocks or []:
        if not isinstance(b, (list, tuple)) or len(b) != 2:
            continue
        s, e = _local(b[0]), _local(b[1])
        if s is None or e is None:
            continue
        t = s.replace(minute=s.minute // 15 * 15, second=0, microsecond=0)
        while t < e:
            out.add((t.strftime("%Y-%m-%d"), t.hour * 4 + t.minute // 15))
            t += timedelta(minutes=15)
    return out


def first_uses(use: dict[str, Any] | None, which: str, blocks: list[Any], events: list[str]) -> dict[date, int]:
    """Per local day: the first quarter it was needed."""
    own = _own(blocks)
    out: dict[date, int] = {}
    for day, kinds in (use or {}).items():
        qs = [q for q in (kinds or {}).get(which, []) if isinstance(q, int) and 0 <= q < Q and (day, q) not in own]
        if not qs:
            continue
        try:
            d = date.fromisoformat(day)
        except ValueError:
            continue
        out[d] = min(qs)
    for iso in events or []:
        t = _local(iso)
        if t is None:
            continue
        q = t.hour * 4 + t.minute // 15
        d = t.date()
        out[d] = min(q, out.get(d, Q))
    return out


def _low(values: list[int]) -> int:
    values = sorted(values)
    return values[len(values) // 4]


def predict(firsts: dict[date, int], use: dict[str, Any] | None = None, which: str = "all",
            blocks: list[Any] | None = None) -> dict[str, Any]:
    """{"week": [{"q", "learned"} × 7 (Mon–Sun)], "learned", "days", "hours": [[share] × 24] × 7}."""
    today = dt_util.as_local(dt_util.utcnow()).date()
    seen = [d for d in [*(firsts or {}), *(date.fromisoformat(k) for k in (use or {}) if _iso(k))] if d <= today]
    first_day = min(seen) if seen else today
    days = max(0, (today - first_day).days)
    per = [[q for d, q in firsts.items() if d.weekday() == wd] for wd in range(7)]
    week = []
    for wd in range(7):
        group = range(5) if wd < 5 else range(5, 7)
        pooled = [q for g in group for q in per[g]]
        every = [q for g in range(7) for q in per[g]]
        if len(per[wd]) >= MIN_SAME:
            week.append({"q": _low(per[wd]), "learned": True})
        elif len(pooled) >= MIN_POOL:
            week.append({"q": _low(pooled), "learned": True})
        elif len(every) >= MIN_POOL:
            week.append({"q": _low(every), "learned": True})
        else:
            week.append({"q": None, "learned": False})
    # How often it was in use per weekday and hour (for the panel's strip).
    own = _own(blocks or [])
    count = [[0] * 24 for _ in range(7)]
    n_days = [0] * 7
    d = first_day
    while d < today:
        n_days[d.weekday()] += 1
        qs = (use or {}).get(d.isoformat(), {}).get(which, []) if use else []
        hours = {q // 4 for q in qs if isinstance(q, int) and 0 <= q < Q and (d.isoformat(), q) not in own}
        if d in firsts:
            hours.add(firsts[d] // 4)
        for h in hours:
            count[d.weekday()][h] += 1
        d += timedelta(days=1)
    share = [[round(count[wd][h] / n_days[wd], 2) if n_days[wd] else 0.0 for h in range(24)] for wd in range(7)]
    return {"week": week, "learned": any(w["learned"] for w in week), "days": days, "hours": share}


def _iso(text: str) -> bool:
    try:
        date.fromisoformat(text)
    except (TypeError, ValueError):
        return False
    return True


def next_need(week: list[dict[str, Any]], now: datetime, fallback_q: int = DEFAULT_Q) -> tuple[datetime, bool]:
    """The next moment (UTC) it is needed, strictly after now, and whether that was learned."""
    local = dt_util.as_local(now)
    for i in range(8):
        day = (local + timedelta(days=i)).date()
        w = week[day.weekday()] if week else {"q": None, "learned": False}
        q = w["q"] if w.get("q") is not None else fallback_q
        at = dt_util.start_of_local_day(day) + timedelta(minutes=15 * q)
        if at > local:
            return dt_util.as_utc(at), bool(w.get("learned"))
    return now + timedelta(days=1), False


def fmt_q(q: int | None) -> str | None:
    return None if q is None else f"{q // 4:02d}:{q % 4 * 15:02d}"


def prune(items: list[Any], now: datetime, end_of: Any = lambda x: x) -> list[Any]:
    since = (now - timedelta(days=KEEP_DAYS)).isoformat()
    return [x for x in items if (end_of(x) or "") >= since]
