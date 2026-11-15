"""What RoomControl learns per room (stored apart from the configuration).

- grace_extra: seconds added to the grace period. Lights that go off for lack
  of motion and are wanted back within GRACE_FALSE_OFF seconds add
  GRACE_STEP_UP; an off that holds (no motion within GRACE_TRUE_OFF) takes
  GRACE_STEP_DOWN off again. Never below 0, never above GRACE_EXTRA_MAX.
- brightness: per lamp and hour of the day, the average brightness (percent)
  people set by hand, with the number of samples. Used as the standard level
  once a lamp has BRIGHT_MIN_SAMPLES for that hour.
- sessions: when the room's lamps were on (start, end, lamps), for the last
  HISTORY_DAYS days. Replayed when nobody is home ("bewoond lijken").
- motion: in how many different hours of each weekday-hour motion was seen,
  since `since`. A weekday-hour that never had motion in at least
  ANOMALY_MIN_WEEKS weeks counts as unusual.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import random
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

LEARN_STORAGE_KEY = "roomcontrol.learn"
LEARN_STORAGE_VERSION = 1
SAVE_DELAY = 30  # s

GRACE_FALSE_OFF = 60  # s: motion this soon after an off → the off was too early
GRACE_TRUE_OFF = 120  # s: no motion this long after an off → the off was right
GRACE_STEP_UP = 60  # s
GRACE_STEP_DOWN = 15  # s
GRACE_EXTRA_MAX = 900  # s

BRIGHT_MIN_SAMPLES = 3
BRIGHT_WEIGHT = 0.3  # weight of a new sample (older ones fade out)

HISTORY_DAYS = 28
SESSION_MIN = 2  # minutes: shorter sessions are not remembered
REPLAY_JITTER = 15  # minutes, ± per day

ANOMALY_MIN_WEEKS = 2


class LearnStore:
    """Learned data of all rooms, saved to .storage/roomcontrol.learn."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, LEARN_STORAGE_VERSION, LEARN_STORAGE_KEY)
        self._data: dict[str, Any] = {"rooms": {}}

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict) and isinstance(stored.get("rooms"), dict):
            self._data = stored

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(lambda: self._data, SAVE_DELAY)

    def room(self, area_id: str) -> dict[str, Any]:
        return self._data["rooms"].setdefault(area_id, {})

    @callback
    def forget(self, area_id: str, what: str) -> None:
        """Forget one kind of learned data of a room (panel: "Opnieuw leren")."""
        room = self.room(area_id)
        if room.pop(what, None) is not None:
            if what == "motion":
                room.pop("motion_since", None)
                room.pop("motion_last", None)
            self._save()

    # ── grace period ───────────────────────────────────────────────────────

    def grace_extra(self, area_id: str) -> int:
        value = self.room(area_id).get("grace_extra", 0)
        return int(value) if isinstance(value, (int, float)) else 0

    @callback
    def grace_feedback(self, area_id: str, seconds_after_off: float) -> int | None:
        """Motion `seconds_after_off` after a no-motion off: learn from it.
        Returns the new extra when it changed."""
        old = self.grace_extra(area_id)
        if seconds_after_off <= GRACE_FALSE_OFF:
            new = min(GRACE_EXTRA_MAX, old + GRACE_STEP_UP)
        elif seconds_after_off >= GRACE_TRUE_OFF:
            new = max(0, old - GRACE_STEP_DOWN)
        else:
            return None
        if new == old:
            return None
        self.room(area_id)["grace_extra"] = new
        self._save()
        return new

    # ── brightness ─────────────────────────────────────────────────────────

    @callback
    def record_brightness(self, area_id: str, lamp: str, hour: int, pct: float) -> None:
        hours = self.room(area_id).setdefault("brightness", {}).setdefault(lamp, {})
        avg, n = hours.get(str(hour), [pct, 0])
        avg = pct if n == 0 else avg * (1 - BRIGHT_WEIGHT) + pct * BRIGHT_WEIGHT
        hours[str(hour)] = [round(avg, 1), n + 1]
        self._save()

    def learned_pct(self, area_id: str, lamp: str, hour: int) -> int | None:
        entry = self.room(area_id).get("brightness", {}).get(lamp, {}).get(str(hour))
        if not entry or entry[1] < BRIGHT_MIN_SAMPLES:
            return None
        return int(min(100, max(1, round(entry[0]))))

    def learned_count(self, area_id: str) -> int:
        """Lamp-hours with enough samples (panel)."""
        return sum(
            1 for hours in self.room(area_id).get("brightness", {}).values()
            for entry in hours.values() if entry[1] >= BRIGHT_MIN_SAMPLES
        )

    # ── sessions (replay) ──────────────────────────────────────────────────

    @callback
    def record_session(self, area_id: str, start: datetime, end: datetime, lamps: list[str]) -> None:
        if (end - start) < timedelta(minutes=SESSION_MIN) or not lamps:
            return
        cutoff = dt_util.utcnow() - timedelta(days=HISTORY_DAYS)
        sessions = [
            s for s in self.room(area_id).get("sessions", [])
            if (t := dt_util.parse_datetime(s[0])) is not None and t >= cutoff
        ]
        sessions.append([start.isoformat(), end.isoformat(), sorted(lamps)])
        self.room(area_id)["sessions"] = sessions
        self._save()

    def session_days(self, area_id: str) -> int:
        """Different days with remembered sessions (panel)."""
        return len({
            dt_util.as_local(t).date() for s in self.room(area_id).get("sessions", [])
            if (t := dt_util.parse_datetime(s[0])) is not None
        })

    def replay_lamps(self, area_id: str, now: datetime) -> set[str]:
        """Lamps that were on at this time on the most recent same weekday with
        sessions, shifted by a per-day random offset of ±REPLAY_JITTER min."""
        local = dt_util.as_local(now)
        today = local.date()
        jitter = random.Random(f"{area_id}{today.isoformat()}").randint(-REPLAY_JITTER, REPLAY_JITTER)
        by_day: dict[Any, list[tuple[datetime, datetime, list[str]]]] = {}
        for s in self.room(area_id).get("sessions", []):
            start, end = dt_util.parse_datetime(s[0]), dt_util.parse_datetime(s[1])
            if start is None or end is None:
                continue
            start, end = dt_util.as_local(start), dt_util.as_local(end)
            if start.date() >= today or start.weekday() != today.weekday():
                continue
            by_day.setdefault(start.date(), []).append((start, end, s[2]))
        if not by_day:
            return set()
        day = max(by_day)
        shift = today - day
        lamps: set[str] = set()
        for start, end, ids in by_day[day]:
            s = start + shift + timedelta(minutes=jitter)
            e = end + shift + timedelta(minutes=jitter)
            if s <= local < e:
                lamps |= set(ids)
        return lamps

    # ── motion pattern (anomalies) ─────────────────────────────────────────

    @callback
    def record_motion(self, area_id: str, now: datetime) -> bool:
        """Count motion once per hour. Returns True when this weekday-hour is
        unusual (never had motion in at least ANOMALY_MIN_WEEKS weeks)."""
        room = self.room(area_id)
        local = dt_util.as_local(now)
        hour_key = local.strftime("%Y-%m-%dT%H")
        if room.get("motion_last") == hour_key:
            return False
        since = dt_util.parse_datetime(room.get("motion_since") or "")
        if since is None:
            room["motion_since"] = now.isoformat()
            since = now
        bucket = f"{local.weekday()}-{local.hour}"
        counts = room.setdefault("motion", {})
        unusual = (now - since) >= timedelta(weeks=ANOMALY_MIN_WEEKS) and not counts.get(bucket)
        counts[bucket] = counts.get(bucket, 0) + 1
        room["motion_last"] = hour_key
        self._save()
        return unusual

    def motion_weeks(self, area_id: str) -> float:
        since = dt_util.parse_datetime(self.room(area_id).get("motion_since") or "")
        return 0 if since is None else round((dt_util.utcnow() - since) / timedelta(weeks=1), 1)
