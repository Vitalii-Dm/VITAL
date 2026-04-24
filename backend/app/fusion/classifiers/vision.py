"""Computer-vision layer classifier — consumes per-zone pose snapshot.

We deliberately stopped using transient "fall" detection (was-standing-then-
horizontal): it's brittle to occlusion and camera angle. Instead, the pose
worker tracks each person and reports how long they've been on the floor.
This classifier just scales concern with that duration.
"""
from __future__ import annotations

from app.fusion.signals import VisionSignal

# Duration → score ladder. flag=True once we cross FLAG_SECONDS.
FLAG_SECONDS = 3.0
_SCORE_LADDER = (
    (20.0, 1.0),
    (10.0, 0.7),
    (3.0, 0.4),
)


def _score_for(seconds: float) -> float:
    for threshold, score in _SCORE_LADDER:
        if seconds >= threshold:
            return score
    return 0.0


def classify_vision(
    horizontal: bool = False,
    max_down_seconds: float = 0.0,
    persons_on_floor_count: int = 0,
    has_person: bool = True,
    standing_count: int = 0,
) -> VisionSignal:
    score = _score_for(max_down_seconds)
    flag = max_down_seconds >= FLAG_SECONDS

    if flag:
        reason = f"person on floor {max_down_seconds:.0f}s"
    else:
        reason = "upright"

    return VisionSignal(
        flag=flag,
        score=score,
        reason=reason,
        horizontal=horizontal,
        has_person=has_person,
        max_down_seconds=max_down_seconds,
        persons_on_floor_count=persons_on_floor_count,
        standing_count=standing_count,
    )
