"""What to do when a zone's severity changes.

Called by `fusion.loop._tick` whenever the severity value for a zone
transitions. Keeps all side-effects (SMS, LED writes, log lines) in one
place so the fusion loop stays pure-ish.
"""
from __future__ import annotations

import asyncio
import logging

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


def _compose_sms(zone: ZoneState, result: FusionResult) -> str:
    reasons = ", ".join(result.reasons) if result.reasons else "multiple layers"
    return f"VITAL — {result.label} in {zone.zone_id}. Reasons: {reasons}"
