"""Pick the most specific `EventType` that the current layer signals justify.

Decision rules (applied in order — first match wins):

    vision.horizontal AND env.heat_stress           → HEAT_EXHAUSTION
    vision.horizontal AND wifi.breathing_anomalous  → CARDIAC
    vision.horizontal AND wifi.still_too_long       → LOSS_OF_CONSCIOUSNESS
    vision.horizontal OR vision.fall_transient      → FALL
    any layer flagged at severity >= MEDIUM         → UNKNOWN_MEDICAL
    (none of the above)                             → NORMAL
"""
from __future__ import annotations

from app.fusion.events import EventType, Severity
from app.fusion.signals import EnvSignal, VisionSignal, WifiSignal


def classify_event(
    wifi: WifiSignal,
    vision: VisionSignal,
    env: EnvSignal,
    severity: Severity,
) -> EventType:
    if severity == Severity.LOW:
        return EventType.NORMAL

    if vision.horizontal and env.heat_stress:
        return EventType.HEAT_EXHAUSTION

    if vision.horizontal and wifi.breathing_anomalous:
        return EventType.CARDIAC

    if vision.horizontal and wifi.still_too_long:
        return EventType.LOSS_OF_CONSCIOUSNESS

    if vision.horizontal or vision.fall_transient:
        return EventType.FALL

    return EventType.UNKNOWN_MEDICAL
