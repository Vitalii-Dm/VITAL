"""Serialize zone + fusion state into the dict broadcast over WebSocket.

Keeping this pure and tiny means the API-level WebSocket message shape can
be tested in isolation (see `tests/test_serializer.py`) and changed in one
place if the frontend needs more/less data.
"""
from __future__ import annotations

import time
from typing import Any

from app.fusion.engine import FusionResult
from app.signal.wetbulb import wet_bulb_c
from app.state import ZoneState

POSE_STALE_AFTER_S = 3.0


def _thin_person(p: dict[str, Any]) -> dict[str, Any]:
    """Pass-through of the fields the dashboard renders — no bbox, no extras."""
    return {
        "track_id": p.get("track_id"),
        "horizontal": bool(p.get("horizontal", False)),
        "down_seconds": float(p.get("down_seconds", 0.0)),
        "keypoints": p.get("keypoints", []),
    }


def build_fusion_payload(zone: ZoneState, result: FusionResult) -> dict[str, Any]:
    persons = [_thin_person(p) for p in zone.last_persons]
    max_down_seconds = max(
        (float(p.get("down_seconds", 0.0)) for p in zone.last_persons),
        default=0.0,
    )

    # pose_stale is undefined (False) until we've ever heard a heartbeat.
    if zone.last_pose_heartbeat > 0:
        pose_stale = (time.time() - zone.last_pose_heartbeat) > POSE_STALE_AFTER_S
    else:
        pose_stale = False

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
        "persons": persons,
        "max_down_seconds": round(max_down_seconds, 1),
        "pose_stale": pose_stale,
    }
