"""When is a device used? Usage windows and an off schedule (step 4b).

From the quarters of an hour a metered switch's device was in use (device
learning "use", last 6 weeks: for a device that keeps warm only real use,
not keep-warm pulses) RoomControl makes per weekday the usage windows: the
quarters used in at least MIN_SHARE of the weeks, with a lead time before
(a device that keeps warm: its heat-up time). Gaps shorter than MIN_OFF_MIN
count as used. Days with the same windows are grouped.

The proposal: off outside the windows, as time slots for the switch's moment
"slot" (room_switches.py), a slot running past midnight where the night is
one gap. Its value per month comes from the device's normal use per hour and
the price per hour (offpay.py); for a device that keeps warm most of what it
saves has to be caught up again (CATCH_UP), at the price when it comes back on.

Room option power[part]["auto_schedule"]: true → once a week RoomControl
writes the proposal into the switch's slots itself (moment "slot" on,
"night" off).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.util import dt as dt_util

MIN_SHARE = 0.2
MIN_OFF_MIN = 120
MIN_DAYS = 14
WARM_LEAD_MIN = 30
CATCH_UP = 0.9
Q = 96  # quarters a day


def _fmt(q: int) -> str:
    q %= Q
    return f"{q // 4:02d}:{q % 4 * 15:02d}"


def usage(offpay: Any, key: str) -> dict[str, Any] | None:
    learner = offpay.learning.learners.get(key)
    if learner is None:
        return None
    kind, _guessed = offpay.kind(key)
    if kind == "cool":
        return {"kind": kind, "enough": False}
    use = learner.data.get("use") or {}
    if not use:
        return {"kind": kind, "enough": False, "days": 0}
    which = "big" if kind == "warm" else "all"
    first = dt_util.parse_datetime(min(use) + "T00:00:00")
    today = dt_util.as_local(dt_util.utcnow()).date()
    first_day = first.date() if first else today
    span = (today - first_day).days
    if span < MIN_DAYS:
        return {"kind": kind, "enough": False, "days": span}
    # Per weekday: how many of those days had use in each quarter.
    days_seen = [0] * 7
    counts = [[0] * Q for _ in range(7)]
    d = first_day
    while d < today:
        days_seen[d.weekday()] += 1
        for q in (use.get(d.isoformat()) or {}).get(which, []):
            if 0 <= q < Q:
                counts[d.weekday()][q] += 1
        d += timedelta(days=1)
    lead = WARM_LEAD_MIN // 15 if kind == "warm" else 0
    used = []
    for wd in range(7):
        n = max(1, days_seen[wd])
        row = [counts[wd][q] / n >= MIN_SHARE for q in range(Q)]
        if lead:
            row = [any(row[(q + i) % Q] for i in range(lead + 1)) for q in range(Q)]
        used.append(row)
    # Fill short gaps (also across midnight) so only long gaps become "off".
    flat = [u for row in used for u in row]
    total = len(flat)
    if any(flat):
        # The week is a circle (Sunday night runs into Monday): start at a used quarter.
        start = flat.index(True)
        k = 0
        while k < total:
            i = (start + k) % total
            if flat[i]:
                k += 1
                continue
            n = 0
            while n < total and not flat[(i + n) % total]:
                n += 1
            if n * 15 < MIN_OFF_MIN:
                for m in range(n):
                    flat[(i + m) % total] = True
            k += n
    used = [flat[wd * Q:(wd + 1) * Q] for wd in range(7)]
    windows = {wd: _runs([q for q in range(Q) if used[wd][q]]) for wd in range(7)}
    groups: list[dict[str, Any]] = []
    for wd in range(7):
        text = [f"{_fmt(a)}–{_fmt(b)}" for a, b in windows[wd]]
        for g in groups:
            if g["windows"] == text:
                g["days"].append(wd)
                break
        else:
            groups.append({"days": [wd], "windows": text})
    # Off slots: the gaps, a gap at the end of a day joined with the next day's first gap.
    slots: dict[tuple[str, str], list[int]] = {}
    for wd in range(7):
        gaps = _runs([q for q in range(Q) if not used[wd][q]])
        nxt = _runs([q for q in range(Q) if not used[(wd + 1) % 7][q]])
        for a, b in gaps:
            if a == 0 and not all(not u for u in used[wd]):
                prev = _runs([q for q in range(Q) if not used[(wd - 1) % 7][q]])
                if prev and prev[-1][1] == Q:
                    continue  # part of yesterday's night slot
            end = b
            if b == Q and nxt and nxt[0][0] == 0:
                end = Q + nxt[0][1]
            if (end - a) * 15 < MIN_OFF_MIN:
                continue
            slots.setdefault((_fmt(a), _fmt(end)), []).append(wd)
    proposal = [{"days": days, "start": {"type": "time", "time": a}, "end": {"type": "time", "time": b}}
                for (a, b), days in sorted(slots.items(), key=lambda kv: (kv[1][0], kv[0]))]
    return {"kind": kind, "enough": True, "days": span, "groups": groups, "proposal": proposal,
            "per_month": _value(offpay, key, kind, used)}


def _runs(qs: list[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for q in qs:
        if out and out[-1][1] == q:
            out[-1] = (out[-1][0], q + 1)
        else:
            out.append((q, q + 1))
    return out


def _value(offpay: Any, key: str, kind: str, used: list[list[bool]]) -> float | None:
    """What off outside the windows would bring per month (€)."""
    from .tariff import buy_now  # noqa: PLC0415

    learner = offpay.learning.learners.get(key)
    hours: dict[str, float] = learner.data.get("hours") or {}
    if not hours:
        return None
    per_hour: dict[int, list[float]] = {}
    for hk, kwh in hours.items():
        per_hour.setdefault(int(hk[-2:]), []).append(kwh)
    base = {h: sorted(v)[len(v) // 2] for h, v in per_hour.items()}
    prices = offpay._profile_prices(buy_now(offpay.hass))
    week = 0.0
    for wd in range(7):
        saved_kwh = saved = 0.0
        for q in range(Q):
            if not used[wd][q]:
                kwh = base.get(q // 4, 0.0) / 4
                saved_kwh += kwh
                saved += kwh * prices[q // 4]
        if kind == "warm":
            on_q = next((q for q in range(Q) if used[wd][q]), 0)
            saved -= CATCH_UP * saved_kwh * prices[on_q // 4]
        week += saved
    return round(week * 30 / 7, 2)
