"""Computer-vision layer classifier — consumes YOLO pose flags."""
from __future__ import annotations

from app.fusion.signals import VisionSignal


def classify_vision(
    horizontal: bool,
    fall_transient: bool,
    has_person: bool = True,
) -> VisionSignal:
    if horizontal:
        return VisionSignal(
            flag=True,
            score=0.9,
            reason="person horizontal",
            horizontal=True,
            fall_transient=fall_transient,
            has_person=has_person,
        )
    if fall_transient:
        return VisionSignal(
            flag=True,
            score=0.6,
            reason="fall transient",
            horizontal=False,
            fall_transient=True,
            has_person=has_person,
        )
    return VisionSignal(
        flag=False, score=0.0, reason="upright", has_person=has_person
    )
