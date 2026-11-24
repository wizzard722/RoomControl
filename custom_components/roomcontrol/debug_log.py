"""The rooms' debug log: what RoomControl did and why, kept for a week.

Each room has its own log (light entity `_debug`), saved to
.storage/roomcontrol.debug_<area id>. An entry:

 {"at": utc iso, "kind": "on" | "off" | "adjust" | "blocked" | "ignored" |
  "info" | "lock" | "door", "reason": "...",
  "bundles": [names],           # what it was about, as shown
  "items": [keys],              # the same as stable keys: "group:<id>" for a
                                # light bundle, else an entity id
  "rules": {key: {"on": [rule, ...], "d": {rule: detail}, "win": rule}},
  ...details (lux, target, pct, why, ...)}

"rules" (light bundles: on, off, adjust, blocked) is the weighing at that
moment: which rules applied and which one decided (see light._rules_for).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN

KEEP_DAYS = 7
MAX_ENTRIES = 6000
SAVE_DELAY = 120  # seconds

# Entries without an item that still belong in an item's own log (context).
ROOM_CONTEXT = {"manual_start", "manual_end", "restart"}

# The rule that decided, from the reason (first match wins) or the "why"
# of a blocked entry.
_WIN_REASON = (
    ("alarm_clock", "clock"),
    ("clock_over", "clock"),
    ("manual", "manual"),
    ("late", "arrive"),
    ("arrive", "arrive"),
    ("alarm_off", "slot"),
    ("alarm_", "alarm"),
    ("lux_", "lux"),
    ("time_slot", "slot"),
    ("own_times", "slot"),
    ("schedule", "slot"),
    ("dusk", "slot"),
    ("no_motion", "motion"),
    ("motion", "motion"),
    ("door", "motion"),
    ("nobody_home", "home"),
    ("conditions", "home"),
    ("replay", "replay"),
    ("restore", "restore"),
    ("restart", "restore"),
    ("external", "external"),
    ("zero_pct", "external"),
    ("brightness_by_hand", "external"),
)
_WIN_WHY = (
    ("manual", "manual"),
    ("armed", "alarm"),
    ("clock", "clock"),
    ("nobody_home", "home"),
    ("late_home", "arrive"),
    ("arrive", "arrive"),
)


def winner(kind: str, reason: str, why: str | None = None) -> str:
    if kind == "blocked" and why:
        for prefix, rule in _WIN_WHY:
            if why.startswith(prefix):
                return rule
    for prefix, rule in _WIN_REASON:
        if reason.startswith(prefix):
            return rule
    return "other"


class DebugBuffer:
    """One room's log, oldest first. `append` is all the writers use."""

    def __init__(self, area_id: str) -> None:
        self.area_id = area_id
        self.entries: list[dict[str, Any]] = []
        self._store: Store[dict[str, Any]] | None = None
        self._loaded = False
        self._pruned_at: str | None = None

    async def async_load(self, hass: HomeAssistant) -> None:
        """Read the saved log and put what was logged meanwhile behind it."""
        self._store = Store(hass, 1, f"{DOMAIN}.debug_{self.area_id}")
        try:
            stored = await self._store.async_load()
        except Exception:  # noqa: BLE001 - a damaged file: start empty
            stored = None
        old = [e for e in (stored or {}).get("entries") or [] if isinstance(e, dict) and isinstance(e.get("at"), str)]
        seen = {(e["at"], e.get("reason")) for e in old}
        self.entries = old + [e for e in self.entries if (e.get("at"), e.get("reason")) not in seen]
        self.entries.sort(key=lambda e: e["at"])
        self._loaded = True
        self._prune(force=True)
        self._save()

    @callback
    def append(self, entry: dict[str, Any]) -> None:
        if not isinstance(entry, dict) or not isinstance(entry.get("at"), str):
            return
        entry.setdefault("items", [])
        entry.setdefault("bundles", [])
        self.entries.append(entry)
        self._prune()
        self._save()

    def __iter__(self):  # noqa: ANN204
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def _prune(self, force: bool = False) -> None:
        if len(self.entries) > MAX_ENTRIES:
            del self.entries[: len(self.entries) - MAX_ENTRIES]
        now = dt_util.utcnow()
        hour = now.strftime("%Y-%m-%dT%H")
        if not force and self._pruned_at == hour:
            return
        self._pruned_at = hour
        cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat()
        drop = 0
        while drop < len(self.entries) and self.entries[drop]["at"] < cutoff:
            drop += 1
        if drop:
            del self.entries[:drop]

    @callback
    def _save(self) -> None:
        if self._loaded and self._store is not None:
            self._store.async_delay_save(lambda: {"entries": self.entries}, SAVE_DELAY)

    # ── reading ────────────────────────────────────────────────────────────

    def newest(self, limit: int = 300, rules: bool = False) -> list[dict[str, Any]]:
        out = self.entries[-limit:] if limit > 0 else list(self.entries)
        if not rules:
            out = [{k: v for k, v in e.items() if k != "rules"} for e in out]
        return list(reversed(out))

    @staticmethod
    def _bounds(day: int) -> tuple[str, str]:
        """UTC iso bounds of local day `day` (0 = today, 1 = yesterday, ...)."""
        start = dt_util.start_of_local_day() - timedelta(days=day)
        end = start + timedelta(days=1)
        return dt_util.as_utc(start).isoformat(), dt_util.as_utc(end).isoformat()

    @staticmethod
    def matches(entry: dict[str, Any], item: str | None, name: str | None) -> bool:
        if not item:
            return True
        items = entry.get("items") or []
        if item in items:
            return True
        if not items:
            if entry.get("reason") in ROOM_CONTEXT:
                return True
            # Entries from before items were kept: by name.
            return bool(name) and name in (entry.get("bundles") or [])
        return False

    def day(self, day: int, item: str | None = None, name: str | None = None) -> list[dict[str, Any]]:
        """One local day of the log (for one item), newest first."""
        start, end = self._bounds(day)
        return [e for e in reversed(self.entries) if start <= e["at"] < end and self.matches(e, item, name)]

    def counts(self, item: str | None = None, name: str | None = None) -> list[int]:
        """Entries per local day, today first (KEEP_DAYS days)."""
        bounds = [self._bounds(d) for d in range(KEEP_DAYS)]
        out = [0] * KEEP_DAYS
        for e in self.entries:
            if not self.matches(e, item, name):
                continue
            for d, (start, end) in enumerate(bounds):
                if start <= e["at"] < end:
                    out[d] += 1
                    break
        return out
