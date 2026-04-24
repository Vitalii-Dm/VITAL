"""Serialize zone + fusion state into the dict broadcast over WebSocket.

Keeping this pure and tiny means the API-level WebSocket message shape can
be tested in isolation (see `tests/test_serializer.py`) and changed in one
place if the frontend needs more/less data.
"""
from __future__ import annotations

from typing import Any

from app.fusion.engine import FusionResult
from app.signal.wetbulb import wet_bulb_c
from app.state import ZoneState


def build_fusion_payload(zone: ZoneState, result: FusionResult) -> dict[str, Any]:
    return {
        "type": "fusion",
        "zone": zone.zone_id,
        "severity": result.severity.value,
        "event": result.event.value,
        "label": result.label,
        "confidence": round(result.confidence, 3),
        "flagged_layers": result.flagged_layers,
        "reasons": result.reasons,
        "timestamp": result.timestamp,
        "bpm": round(zone.last_bpm, 1),
        "temp_c": round(zone.last_temp_c, 1),
        "rh_pct": round(zone.last_rh_pct, 1),
        "wetbulb_c": round(wet_bulb_c(zone.last_temp_c, zone.last_rh_pct), 1),
        "waveform": list(zone.waveform),
    }
