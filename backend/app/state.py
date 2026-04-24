"""In-memory world state — zones, latest readings, active alerts.

Swap for Redis/Postgres post-hackathon. For the 3-min demo, RAM is enough.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

from app.fusion.engine import FusionResult
from app.signal.breathing import BreathingExtractor
from app.signal.motion import MotionDetector, MotionState


@dataclass
class ZoneState:
    zone_id: str
    breathing: BreathingExtractor = field(default_factory=BreathingExtractor)
    motion: MotionDetector = field(default_factory=MotionDetector)
    last_motion: MotionState | None = None
    last_bpm: float = 0.0
    last_temp_c: float = 20.0
    last_rh_pct: float = 50.0
    last_vision_horizontal: bool = False
    last_vision_fall: bool = False
    last_fusion: FusionResult | None = None
    waveform: deque[float] = field(default_factory=lambda: deque(maxlen=280))  # 10s @ 28Hz
    updated_at: float = field(default_factory=time.time)


class WorldState:
    def __init__(self) -> None:
        self._zones: dict[str, ZoneState] = {}

    def zone(self, zone_id: str) -> ZoneState:
        if zone_id not in self._zones:
            self._zones[zone_id] = ZoneState(zone_id=zone_id)
        return self._zones[zone_id]

    def all_zones(self) -> list[ZoneState]:
        return list(self._zones.values())


world = WorldState()
