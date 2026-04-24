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

    persons = zone.last_persons
    any_horizontal = any(bool(p.get("horizontal", False)) for p in persons)
    downs = [float(p.get("down_seconds", 0.0)) for p in persons]
    max_down = max(downs, default=0.0)
    on_floor_count = sum(1 for d in downs if d > 0.0)
    # Standing is informational — "upright worker" count per zone. Falls back
    # to False for any person dict emitted by a pre-standing pose worker.
    standing_count = sum(1 for p in persons if bool(p.get("standing", False)))
    vision = classify_vision(
        horizontal=any_horizontal,
        max_down_seconds=max_down,
        persons_on_floor_count=on_floor_count,
        has_person=bool(persons),
        standing_count=standing_count,
    )

    wbt = wet_bulb_c(zone.last_temp_c, zone.last_rh_pct)
    env = classify_env(zone.last_temp_c, zone.last_rh_pct, wbt)
    return fuse(wifi, vision, env)
