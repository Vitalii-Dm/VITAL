"""What to do when a zone's severity changes.

Called by `fusion.loop._tick` whenever the severity value for a zone
transitions. Keeps all side-effects (SMS, LED writes, log lines) in one
place so the fusion loop stays pure-ish.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Awaitable, Callable

from app.alerts.led_strip import AMBER, GREEN, RED, set_zone_color
from app.alerts.twilio_sms import send_supervisor_sms
from app.fusion.engine import FusionResult
from app.fusion.events import Severity
from app.state import ZoneState

log = logging.getLogger(__name__)

_SEVERITY_COLOR = {
    Severity.LOW: GREEN,
    Severity.MEDIUM: AMBER,
    Severity.HIGH: RED,
}

# One-shot debounce: don't re-fire the emergency pipeline more often than this.
EMERGENCY_REFIRE_COOLDOWN_S = 60.0

# Future ElevenLabs / 911 pipeline hook. Subscribers are called with
# (zone, result) when an emergency is dispatched. Fire-and-forget.
EmergencySubscriber = Callable[[ZoneState, FusionResult], Awaitable[None]]
_emergency_subscribers: list[EmergencySubscriber] = []


def subscribe_emergency(cb: EmergencySubscriber) -> None:
    """Register a coroutine called on each emergency_dispatch."""
    _emergency_subscribers.append(cb)


async def on_severity_change(
    zone: ZoneState, result: FusionResult, previous: Severity
) -> None:
    log.info(
        "zone=%s severity %s → %s event=%s",
        zone.zone_id,
        previous.value,
        result.severity.value,
        result.event.value,
    )

    set_zone_color(zone.zone_id, _SEVERITY_COLOR[result.severity])

    if result.severity == Severity.HIGH and previous != Severity.HIGH:
        # Fire-and-forget: don't block the fusion loop on network I/O.
        asyncio.create_task(
            send_supervisor_sms(_compose_sms(zone, result)),
            name=f"sms-{zone.zone_id}",
        )

    _maybe_dispatch_emergency(zone, result)


def _maybe_dispatch_emergency(zone: ZoneState, result: FusionResult) -> None:
    """One-shot emergency event when HIGH is reached via the 20 s floor path.

    Debounced per-zone so we don't flood the downstream pipeline on every
    fusion tick while a worker is still on the floor.
    """
    if not result.emergency_override:
        return

    now = time.time()
    if now - zone.last_emergency_dispatch_ts < EMERGENCY_REFIRE_COOLDOWN_S:
        return
    zone.last_emergency_dispatch_ts = now

    max_down = 0.0
    for r in result.reasons:
        # Pick out "person on floor Ns" if present; else leave 0.
        if r.startswith("person on floor"):
            try:
                max_down = float(r.rsplit(" ", 1)[-1].rstrip("s"))
            except ValueError:
                pass

    reason_str = "; ".join(result.reasons) or "on-floor timer"
    log.warning(
        "EMERGENCY_DISPATCH zone=%s reason=%s down_seconds=%.1f",
        zone.zone_id,
        reason_str,
        max_down,
    )

    for cb in _emergency_subscribers:
        asyncio.create_task(cb(zone, result), name=f"emergency-{zone.zone_id}")


def _compose_sms(zone: ZoneState, result: FusionResult) -> str:
    reasons = ", ".join(result.reasons) if result.reasons else "multiple layers"
    return f"VITAL — {result.label} in {zone.zone_id}. Reasons: {reasons}"
