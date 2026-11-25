"""Prediction model per room: will the room be in use soon?

Every minute RoomControl takes a snapshot of each room and, a quarter of an
hour later, notes whether the room was in use in that quarter (motion on its
own sensors, or one of its lamps on). Two small models learn from this, by
online logistic regression on one-hot features (light enough for a Pi, and
explainable: each feature has a weight):

- "now": the chance the room is in use in the next 15 minutes, from the time
  slot (workday / weekend × hour), who of the household is home, how long ago
  the last motion here was, motion in linked rooms, lamps on, media playing
  and dark outside;
- "day": the chance the room is in use in a quarter of the day, from the time
  slot, who is home and dark only (to draw today's timeline ahead).

A room with less than POOL_DAYS days learned borrows the day model of its
linked rooms for the timeline.

How sure: every snapshot's prediction is checked when its quarter is over.
Per day RoomControl keeps how often "in use" and "not in use" were predicted
right; the certainty is the balanced accuracy (the mean of both hit rates:
50 % = guessing) over the last CONF_DAYS days. It is shown only; nothing
acts on it yet. Kept in .storage/roomcontrol.predict.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
import logging
import math
from typing import Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.predict"
HORIZON = 15  # minutes ahead
LR = 0.05
L2 = 0.0005
CONF_DAYS = 7
KEEP_DAYS = 30
POOL_DAYS = 3
SINCE_BUCKETS = ((5, "0-5"), (15, "5-15"), (60, "15-60"), (240, "60-240"))
LINKED_MIN = 5


def _sig(z: float) -> float:
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


class Model:
    """Logistic regression on one-hot (string) features."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.w: dict[str, float] = {k: float(v) for k, v in (data.get("w") or {}).items()}
        self.b = float(data.get("b") or 0.0)
        self.n = int(data.get("n") or 0)

    def dump(self) -> dict[str, Any]:
        return {"w": {k: round(v, 4) for k, v in self.w.items() if abs(v) > 1e-4}, "b": round(self.b, 4), "n": self.n}

    def z(self, feats: list[str]) -> float:
        return self.b + sum(self.w.get(f, 0.0) for f in feats)

    def p(self, feats: list[str]) -> float:
        return _sig(self.z(feats))

    def learn(self, feats: list[str], y: int) -> None:
        err = y - self.p(feats)
        self.b += LR * err
        for f in feats:
            w = self.w.get(f, 0.0)
            self.w[f] = w + LR * (err - L2 * w)
        self.n += 1


class RoomPredictor:
    """The models and checks of one room."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.now = Model(data.get("now"))
        self.day = Model(data.get("day"))
        self.first: str | None = data.get("first")
        self.conf: dict[str, list[int]] = {k: list(v) for k, v in (data.get("conf") or {}).items()
                                           if isinstance(v, list) and len(v) == 4}  # day: tp, fp, tn, fn
        self.today: dict[str, Any] = data.get("today") or {}  # {"day", "motion": [q], "lamps": [q]}
        self.pending: deque[tuple[datetime, list[str], list[str], float]] = deque()
        self.used: deque[tuple[datetime, bool]] = deque()

    def dump(self) -> dict[str, Any]:
        return {"now": self.now.dump(), "day": self.day.dump(), "first": self.first, "conf": self.conf, "today": self.today}

    def days(self) -> int:
        if not self.first:
            return 0
        try:
            first = datetime.fromisoformat(self.first).date()
        except ValueError:
            return 0
        return max(0, (dt_util.as_local(dt_util.utcnow()).date() - first).days)

    def certainty(self) -> tuple[float | None, list[dict[str, Any]]]:
        """Balanced accuracy over the last CONF_DAYS days, and per day (for the panel)."""
        keys = sorted(self.conf)[-KEEP_DAYS:]

        def ba(tp: int, fp: int, tn: int, fn: int) -> float | None:
            if tp + fn == 0 or tn + fp == 0:
                return None
            return (tp / (tp + fn) + tn / (tn + fp)) / 2

        per_day = [{"day": k, "value": None if (v := ba(*self.conf[k])) is None else round(v * 100)} for k in keys]
        last = keys[-CONF_DAYS:]
        tot = [sum(self.conf[k][i] for k in last) for i in range(4)]
        v = ba(*tot) if last else None
        return (None if v is None else round(v * 100), per_day)


class Predictor:
    """Takes the snapshots of all rooms and keeps their models."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, STORAGE_KEY)
        self.rooms: dict[str, RoomPredictor] = {}
        self._unsub: CALLBACK_TYPE | None = None

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        for area, value in (data.get("rooms") or {}).items():
            if isinstance(value, dict):
                self.rooms[area] = RoomPredictor(value)

    def _save(self) -> None:
        self._store.async_delay_save(lambda: {"rooms": {a: r.dump() for a, r in self.rooms.items()}}, 120)

    @callback
    def start(self) -> None:
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))

    @callback
    def shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        self._save()

    # ── features ───────────────────────────────────────────────────────────

    def _light(self, area: str) -> Any:
        return self.hass.data.get(DOMAIN, {}).get("entities", {}).get(area)

    def _persons(self) -> list[str]:
        from .rooms import household_persons  # noqa: PLC0415

        return household_persons(self.hass)

    def _home(self) -> list[str]:
        return [f"person:{p}" for p in self._persons() if (st := self.hass.states.get(p)) is not None and st.state == "home"]

    def _dark(self) -> bool:
        st = self.hass.states.get("sun.sun")
        return st is not None and st.state == "below_horizon"

    @staticmethod
    def _slot(when: datetime) -> str:
        local = dt_util.as_local(when)
        return f"slot:{'we' if local.weekday() >= 5 else 'wd'}:{local.hour}"

    def _state(self, area: str, now: datetime) -> dict[str, Any] | None:
        """What the room is doing now: motion, lamps, media, last motion."""
        light = self._light(area)
        if light is None:
            return None
        try:
            motion = bool(light._own_motion())
            lamps = any((st := self.hass.states.get(e)) is not None and st.state == "on" for e in light._members)
            media = bool(light._media_active())
            last = light._last_motion_at
        except Exception:  # noqa: BLE001 - a room that can't be read now
            return None
        since = 0.0 if motion else max(0.0, (now - last).total_seconds() / 60) if last else 1e9
        return {"motion": motion, "lamps": lamps, "media": media, "since": since}

    def _linked_motion(self, area: str, now: datetime) -> bool:
        from .rooms import linked_group  # noqa: PLC0415

        for other in linked_group(self.hass, area):
            if other == area:
                continue
            light = self._light(other)
            try:
                if light is not None and (light._own_motion()
                                          or (now - light._last_motion_at) <= timedelta(minutes=LINKED_MIN)):
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def features(self, area: str, now: datetime, state: dict[str, Any]) -> tuple[list[str], list[str]]:
        home, dark = self._home(), self._dark()
        since = next((name for limit, name in SINCE_BUCKETS if state["since"] < limit), "240+")
        now_f = [self._slot(now), *home, f"since:{since}"]
        if not home:
            now_f.append("nobody")
        if self._linked_motion(area, now):
            now_f.append("linked")
        if state["lamps"]:
            now_f.append("lamps")
        if state["media"]:
            now_f.append("media")
        if dark:
            now_f.append("dark")
        day_f = [self._slot(now), *home, *(["nobody"] if not home else []), *(["dark"] if dark else [])]
        return now_f, day_f

    # ── learning ───────────────────────────────────────────────────────────

    @callback
    def _tick(self, _now: Any = None) -> None:
        from .rooms import managed_areas  # noqa: PLC0415

        now = dt_util.utcnow().replace(second=0, microsecond=0)
        try:
            areas = managed_areas(self.hass)
        except Exception:  # noqa: BLE001
            return
        for area in areas:
            state = self._state(area, now)
            if state is None:
                continue
            room = self.rooms.setdefault(area, RoomPredictor())
            local = dt_util.as_local(now)
            if room.first is None:
                room.first = local.date().isoformat()
            used = state["motion"] or state["lamps"]
            room.used.append((now, used))
            while room.used and now - room.used[0][0] > timedelta(minutes=HORIZON + 2):
                room.used.popleft()
            self._note_today(room, local, state)
            now_f, day_f = self.features(area, now, state)
            room.pending.append((now, now_f, day_f, room.now.p(now_f)))
            # Snapshots whose quarter is over: was the room used in it?
            while room.pending and now - room.pending[0][0] >= timedelta(minutes=HORIZON):
                t, nf, df, p = room.pending.popleft()
                y = int(any(u for when, u in room.used if t < when <= t + timedelta(minutes=HORIZON)))
                room.now.learn(nf, y)
                room.day.learn(df, y)
                self._check(room, t, p, y)
        if now.minute % 10 == 0:
            self._save()

    @staticmethod
    def _note_today(room: RoomPredictor, local: datetime, state: dict[str, Any]) -> None:
        day = local.date().isoformat()
        if room.today.get("day") != day:
            room.today = {"day": day, "motion": [], "lamps": []}
        q = local.hour * 4 + local.minute // 15
        for key in ("motion", "lamps"):
            if state[key] and q not in room.today[key]:
                room.today[key].append(q)

    @staticmethod
    def _check(room: RoomPredictor, when: datetime, p: float, y: int) -> None:
        day = dt_util.as_local(when).date().isoformat()
        c = room.conf.setdefault(day, [0, 0, 0, 0])
        guess = p >= 0.5
        c[0 if guess and y else 1 if guess else 3 if y else 2] += 1
        if len(room.conf) > KEEP_DAYS:
            for old in sorted(room.conf)[:-KEEP_DAYS]:
                room.conf.pop(old, None)

    # ── for the panel ──────────────────────────────────────────────────────

    def _day_model(self, area: str) -> Model:
        """The room's day model, or (still new) the mean of its linked rooms' that know more."""
        from .rooms import linked_group  # noqa: PLC0415

        room = self.rooms.get(area) or RoomPredictor()
        if room.days() >= POOL_DAYS:
            return room.day
        others = [r.day for a in linked_group(self.hass, area)
                  if a != area and (r := self.rooms.get(a)) is not None and r.days() >= POOL_DAYS]
        if not others:
            return room.day
        pooled = Model()
        keys = {k for m in others for k in m.w}
        pooled.w = {k: sum(m.w.get(k, 0.0) for m in others) / len(others) for k in keys}
        pooled.b = sum(m.b for m in others) / len(others)
        return pooled

    def _label(self, feat: str) -> dict[str, Any]:
        kind, _, rest = feat.partition(":")
        if kind == "person":
            st = self.hass.states.get(rest)
            return {"kind": "person", "name": (st.attributes.get("friendly_name") if st else None) or rest}
        if kind == "slot":
            part, hour = rest.split(":")
            return {"kind": "slot", "we": part == "we", "hour": int(hour)}
        if kind == "since":
            return {"kind": "since", "bucket": rest}
        return {"kind": feat}

    def status(self, area: str) -> dict[str, Any]:
        from .rooms import linked_group  # noqa: PLC0415

        room = self.rooms.get(area) or RoomPredictor()
        now = dt_util.utcnow().replace(second=0, microsecond=0)
        state = self._state(area, now) or {"motion": False, "lamps": False, "media": False, "since": 1e9}
        now_f, _day_f = self.features(area, now, state)
        p_now = room.now.p(now_f)
        # What weighs most now: the chance without that feature, compared.
        why = []
        for f in now_f:
            without = _sig(room.now.z(now_f) - room.now.w.get(f, 0.0))
            effect = p_now - without
            if abs(effect) >= 0.02:
                why.append({**self._label(f), "effect": round(effect * 100)})
        why.sort(key=lambda w: -abs(w["effect"]))
        # Today's timeline: the day model per quarter (who is home as now).
        day = self._day_model(area)
        home = self._home()
        start = dt_util.start_of_local_day()
        timeline = []
        for q in range(96):
            t = start + timedelta(minutes=15 * q)
            f = [self._slot(t), *home, *(["nobody"] if not home else [])]
            sun = self.hass.states.get("sun.sun")
            if sun is not None:
                rising = dt_util.parse_datetime(str(sun.attributes.get("next_rising") or ""))
                setting = dt_util.parse_datetime(str(sun.attributes.get("next_setting") or ""))
                if rising and setting and self._dark_at(t, rising, setting):
                    f.append("dark")
            timeline.append(round(day.p(f) * 100))
        local = dt_util.as_local(now)
        ahead = []
        for h in range(1, 5):
            t = local.replace(minute=0) + timedelta(hours=h)
            qs = [timeline[(t.hour * 4 + i) % 96] for i in range(4)] if t.date() == local.date() else [
                round(day.p([self._slot(t), *home, *(["nobody"] if not home else [])]) * 100)]
            ahead.append({"at": dt_util.as_utc(t).isoformat(), "p": round(sum(qs) / len(qs))})
        certainty, per_day = room.certainty()
        light = self._light(area)
        remaining = self._remaining(area, light, now) if (state["lamps"] or state["motion"]) else None
        return {
            "area_id": area, "days": room.days(), "samples": room.now.n, "p_now": round(p_now * 100), "in_use": bool(state["motion"] or state["lamps"]),
            "remaining_min": remaining, "why": why[:6], "timeline": timeline, "ahead": ahead,
            "today": {"motion": sorted(room.today.get("motion", [])) if room.today.get("day") == local.date().isoformat() else [],
                      "lamps": sorted(room.today.get("lamps", [])) if room.today.get("day") == local.date().isoformat() else []},
            "now_q": local.hour * 4 + local.minute // 15,
            "certainty": certainty, "per_day": per_day,
            "pooled": room.days() < POOL_DAYS and any(a != area and (r := self.rooms.get(a)) is not None and r.days() >= POOL_DAYS
                                                      for a in linked_group(self.hass, area)),
            "linked": [a for a in linked_group(self.hass, area) if a != area],
        }

    @staticmethod
    def _dark_at(t: datetime, rising: datetime, setting: datetime) -> bool:
        """Roughly dark at t, from today's next rising and setting (same times every day)."""
        local = dt_util.as_local(t)
        r, s = dt_util.as_local(rising), dt_util.as_local(setting)
        minutes = local.hour * 60 + local.minute
        return not (r.hour * 60 + r.minute <= minutes < s.hour * 60 + s.minute)

    def _remaining(self, area: str, light: Any, now: datetime) -> int | None:
        """How long the lamps probably stay on: the median of what the sessions that
        lasted at least this long still lasted (learn.py sessions, 28 days)."""
        learn = self.hass.data.get(DOMAIN, {}).get("learn")
        start = getattr(light, "_session_start", None) if light is not None else None
        if learn is None or start is None:
            return None
        elapsed = (now - start).total_seconds() / 60
        rest = []
        for s in learn.room(area).get("sessions", []):
            a, b = dt_util.parse_datetime(s[0]), dt_util.parse_datetime(s[1])
            if a and b and (b - a).total_seconds() / 60 >= elapsed:
                rest.append((b - a).total_seconds() / 60 - elapsed)
        if len(rest) < 3:
            return None
        rest.sort()
        return round(rest[len(rest) // 2])
