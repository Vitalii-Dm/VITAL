"""Per-layer signal dataclasses produced by the classifiers.

Each layer (WiFi CSI, computer vision, environment) outputs a structured
signal. The fusion engine and the event classifier operate on these
dataclasses — never on free-form strings — so the decision logic is easy
to unit-test and impossible to fool by rewording a `reason` field.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LayerSignal:
    """Common shape every classifier returns."""

    flag: bool
    score: float  # 0..1 — how concerning this layer thinks the state is
    reason: str   # human-readable summary (UI display only, never parsed)


@dataclass
class WifiSignal(LayerSignal):
    bpm: float = 0.0
    moving: bool = True
    seconds_still: float = 0.0
    breathing_anomalous: bool = False   # bpm out of healthy band
    still_too_long: bool = False        # stillness past the configured threshold


@dataclass
class VisionSignal(LayerSignal):
    horizontal: bool = False            # any person lying horizontally
    has_person: bool = False
    max_down_seconds: float = 0.0       # longest on-floor duration across persons
    persons_on_floor_count: int = 0     # how many distinct tracks are on the floor
    standing_count: int = 0             # how many distinct tracks are upright (informational)


@dataclass
class EnvSignal(LayerSignal):
    temp_c: float = 0.0
    rh_pct: float = 0.0
    wetbulb_c: float = 0.0
    heat_stress: bool = False
