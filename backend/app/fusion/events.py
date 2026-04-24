from __future__ import annotations

from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventType(str, Enum):
    NORMAL = "normal"
    FALL = "fall"
    HEAT_EXHAUSTION = "heat_exhaustion"
    CARDIAC = "cardiac"
    LOSS_OF_CONSCIOUSNESS = "loss_of_consciousness"
    UNKNOWN_MEDICAL = "unknown_medical"


EVENT_LABELS: dict[EventType, str] = {
    EventType.NORMAL: "Normal",
    EventType.FALL: "Fall detected",
    EventType.HEAT_EXHAUSTION: "Heat exhaustion probable",
    EventType.CARDIAC: "Possible cardiac event",
    EventType.LOSS_OF_CONSCIOUSNESS: "Loss of consciousness",
    EventType.UNKNOWN_MEDICAL: "Unknown medical event",
}
