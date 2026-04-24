"""Run the three classifiers on one zone's latest state → FusionResult."""
from __future__ import annotations

from app.fusion.classifiers import classify_env, classify_vision, classify_wifi
from app.fusion.engine import FusionResult, fuse
from app.signal.wetbulb import wet_bulb_c
from app.state import ZoneState


def fuse_zone(zone: ZoneState) -> FusionResult:
    wifi = classify_wifi(
        bpm=zone.last_bpm,
        moving=(zone.last_motion.moving if zone.last_motion else True),
        seconds_still=(zone.last_motion.seconds_still if zone.last_motion else 0.0),
    )
    vision = classify_vision(
        horizontal=zone.last_vision_horizontal,
        fall_transient=zone.last_vision_fall,
    )
    wbt = wet_bulb_c(zone.last_temp_c, zone.last_rh_pct)
    env = classify_env(zone.last_temp_c, zone.last_rh_pct, wbt)
    return fuse(wifi, vision, env)
