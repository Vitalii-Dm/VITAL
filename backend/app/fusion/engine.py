"""Combine three layer signals into one `FusionResult`.

This module is intentionally tiny — the interesting logic lives in:

  - `classifiers/` — how raw sensor data becomes a LayerSignal
  - `event_classifier.py` — how signals map to an EventType

`fuse()` only decides severity (LOW/MEDIUM/HIGH) from the number of flagged
layers, computes a combined confidence, and delegates event type.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.fusion.event_classifier import classify_event
from app.fusion.events import EVENT_LABELS, EventType, Severity
from app.fusion.signals import EnvSignal, VisionSignal, WifiSignal


@dataclass
class FusionResult:
    severity: Severity
    event: EventType
    label: str
    confidence: float
    flagged_layers: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


def _severity_from_flag_count(n_flagged: int) -> Severity:
    if n_flagged >= 3:
        return Severity.HIGH
    if n_flagged == 2:
        return Severity.MEDIUM
    return Severity.LOW


def _combined_confidence(*scores: float) -> float:
    positive = [s for s in scores if s > 0]
    return sum(positive) / len(positive) if positive else 0.0


def fuse(wifi: WifiSignal, vision: VisionSignal, env: EnvSignal) -> FusionResult:
    named = (("wifi", wifi), ("vision", vision), ("env", env))
    flagged_layers = [name for name, sig in named if sig.flag]
    reasons = [sig.reason for _, sig in named if sig.flag]

    severity = _severity_from_flag_count(len(flagged_layers))
    confidence = _combined_confidence(wifi.score, vision.score, env.score)
    event = classify_event(wifi, vision, env, severity)

    return FusionResult(
        severity=severity,
        event=event,
        label=EVENT_LABELS[event],
        confidence=confidence,
        flagged_layers=flagged_layers,
        reasons=reasons,
    )
