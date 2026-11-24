"""Watching metered devices: done, cooling, forgotten (on top of device_learning).

Per device (switch or meter with a power sensor), room option "power":
{part key: {"watch": {"done": bool,        # message when a run is over (someone home)
                      "cool": bool,        # fridge / freezer: no power for COOL_OFF_MIN,
                                           # or a week clearly above normal
                      "forgot": bool,      # running longer than the time limit
                      "forgot_hours": h}}} # the limit; none: 2× its longest learned run, at least 2 h

Where messages go, general setting "device_notify":
{"ha": bool (default on: a melding in Home Assistant),
 "phone": bool, "persons": [person ids] ([] = everyone RoomControl follows),
 "nspanel": "none" | "all" | group id}
Each message is also noted in the room's "What happened".
"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .nspanel import nspanel_message
from .person_notify import person_notify_service
from .rooms import anyone_home

_LOGGER = logging.getLogger(__name__)

COOL_OFF_MIN = 30
COOL_MORE = 1.3  # a week this much above the 4 weeks before
FORGOT_MIN_H = 2.0

_TEXT = {
    "nl": {
        "title": "Apparaten",
        "done": "{name} is klaar{detail}.",
        "cool_off": "{name} verbruikt al {min} minuten niets. Staat hij nog aan?",
        "cool_more": "{name} verbruikte de afgelopen week {pct}% meer dan normaal ({kwh} kWh).",
        "forgot": "{name} staat al {dur} aan.",
    },
    "en": {
        "title": "Devices",
        "done": "{name} is done{detail}.",
        "cool_off": "{name} has used no power for {min} minutes. Is it still on?",
        "cool_more": "{name} used {pct}% more than normal over the last week ({kwh} kWh).",
        "forgot": "{name} has been on for {dur}.",
    },
}


def _lang(hass: HomeAssistant) -> str:
    return "nl" if (hass.config.language or "").lower().startswith("nl") else "en"


def _num(value: Any) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _dur(hours: float, lang: str) -> str:
    h, m = int(hours), int(round((hours - int(hours)) * 60))
    if m == 60:
        h, m = h + 1, 0
    return f"{h}:{m:02d} {'uur' if lang == 'nl' else 'h'}"


class DeviceWatch:
    """Sends the messages; device_learning tells it about finished runs."""

    def __init__(self, hass: HomeAssistant, learning: Any) -> None:
        self.hass = hass
        self.learning = learning
        self._unsub: CALLBACK_TYPE | None = None

    @callback
    def start(self) -> None:
        self._unsub = async_track_time_interval(self.hass, self._tick, timedelta(minutes=1))

    @callback
    def shutdown(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ── config ─────────────────────────────────────────────────────────────

    def _room(self, key: str) -> tuple[str, str, dict[str, Any]] | None:
        area, _, part = key.partition("|")
        for room in self.hass.data.get(DOMAIN, {}).get("rooms", []):
            if room.get("area_id") == area:
                return area, part, room
        return None

    def watch(self, key: str) -> dict[str, Any]:
        found = self._room(key)
        if found is None:
            return {}
        _area, part, room = found
        conf = (room.get("power") or {}).get(part) or {}
        watch = conf.get("watch")
        return watch if isinstance(watch, dict) else {}

    def _program_name(self, key: str, pid: str | None) -> str | None:
        found = self._room(key)
        if found is None or not pid:
            return None
        _area, part, room = found
        names = ((room.get("power") or {}).get(part) or {}).get("programs") or {}
        return names.get(pid)

    def forgot_limit(self, key: str) -> float:
        """Hours after which a run counts as forgotten."""
        watch = self.watch(key)
        hours = watch.get("forgot_hours")
        if isinstance(hours, (int, float)) and hours > 0:
            return float(hours)
        learner = self.learning.learners.get(key)
        longest = max((c["min"] for c in (learner.data["cycles"] if learner else [])), default=0) / 60
        return max(FORGOT_MIN_H, 2 * longest)

    # ── sending ────────────────────────────────────────────────────────────

    def _send(self, key: str, kind: str, message: str) -> None:
        cfg = self.hass.data.get(DOMAIN, {}).get("settings", {}).get("device_notify") or {}
        lang = _lang(self.hass)
        title = _TEXT[lang]["title"]
        if cfg.get("ha", True):
            persistent_notification.async_create(self.hass, message, title=title,
                                                 notification_id=f"{DOMAIN}_device_{kind}_{key}".replace("|", "_").replace(":", "_").replace(".", "_"))
        if cfg.get("phone"):
            persons = [p for p in cfg.get("persons") or [] if p] or list(
                self.hass.data.get(DOMAIN, {}).get("settings", {}).get("persons") or [])
            services = {s for p in persons if (s := person_notify_service(self.hass, p))}
            for service in services:
                self.hass.async_create_task(self.hass.services.async_call(
                    "notify", service.split(".", 1)[1], {"title": title, "message": message}, blocking=False))
        target = cfg.get("nspanel") or "none"
        if target != "none":
            nspanel_message(self.hass, "devices", message, title=title, target=target)
        found = self._room(key)
        light = self.hass.data.get(DOMAIN, {}).get("entities", {}).get(found[0]) if found else None
        if light is not None and hasattr(light, "_debug"):
            light._debug.append({"at": dt_util.utcnow().isoformat(), "kind": "info", "reason": f"device_{kind}",
                                 "bundles": [self.learning.names.get(key, key)],
                                 "items": [key.partition("|")[2] or key]})
        _LOGGER.debug("Device message (%s): %s", kind, message)

    # ── events ─────────────────────────────────────────────────────────────

    @callback
    def run_done(self, key: str, cycle: dict[str, Any]) -> None:
        """A run is over: "done" message when someone is home."""
        if not self.watch(key).get("done") or not anyone_home(self.hass):
            return
        lang = _lang(self.hass)
        from .tariff import buy_now  # noqa: PLC0415

        parts = []
        if name := self._program_name(key, cycle.get("prog")):
            parts.append(name)
        parts.append(f"{_num(cycle['kwh'])} kWh".replace(".", "," if lang == "nl" else "."))
        if (price := buy_now(self.hass)) is not None:
            parts.append(f"€ {cycle['kwh'] * price:.2f}".replace(".", "," if lang == "nl" else "."))
        detail = f" ({' · '.join(parts)})"
        name = self.learning.names.get(key, key)
        self._send(key, "done", _TEXT[lang]["done"].format(name=name, detail=detail))

    @callback
    def _tick(self, _now: Any = None) -> None:
        now = dt_util.utcnow()
        lang = _lang(self.hass)
        for key, sensor in list(self.learning.sensors.items()):
            learner = self.learning.learners.get(key)
            if learner is None:
                continue
            watch = self.watch(key)
            name = self.learning.names.get(key, key)
            d = learner.data
            if watch.get("cool"):
                st = self.hass.states.get(sensor)
                try:
                    zero = st is None or float(st.state) <= 0.5
                except (TypeError, ValueError):
                    zero = True  # unavailable / unknown
                if zero:
                    since = d.get("zero_since")
                    if since is None:
                        d["zero_since"] = now.isoformat()
                    elif not d.get("zero_sent") and (now - dt_util.parse_datetime(since)).total_seconds() >= COOL_OFF_MIN * 60:
                        d["zero_sent"] = True
                        self._send(key, "cool_off", _TEXT[lang]["cool_off"].format(name=name, min=COOL_OFF_MIN))
                else:
                    d.pop("zero_since", None)
                    d.pop("zero_sent", None)
                # Once a week: the last 7 days against the 28 before.
                week = now.strftime("%G-W%V")
                if d.get("week_checked") != week:
                    d["week_checked"] = week
                    local = dt_util.as_local(now)
                    last = sum(d["days"].get((local - timedelta(days=i)).strftime("%Y-%m-%d"), 0.0) for i in range(1, 8))
                    before_days = [d["days"].get((local - timedelta(days=i)).strftime("%Y-%m-%d")) for i in range(8, 36)]
                    before = [v for v in before_days if v is not None]
                    if len(before) >= 21:
                        normal = sum(before) / len(before) * 7
                        if normal > 0 and last > normal * COOL_MORE:
                            pct = round((last / normal - 1) * 100)
                            self._send(key, "cool_more", _TEXT[lang]["cool_more"].format(
                                name=name, pct=pct, kwh=_num(last).replace(".", "," if lang == "nl" else ".")))
            if watch.get("forgot") and learner.run is not None:
                hours = (now.timestamp() - learner.run["start"]) / 3600
                if hours >= self.forgot_limit(key) and learner.run.get("forgot_sent") is None:
                    learner.run["forgot_sent"] = True
                    self._send(key, "forgot", _TEXT[lang]["forgot"].format(name=name, dur=_dur(hours, lang)))
