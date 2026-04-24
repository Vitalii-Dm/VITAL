"""WiFi-CSI layer classifier — consumes breathing rate + motion state."""
from __future__ import annotations

from app.config import settings
from app.fusion.signals import WifiSignal


def classify_wifi(bpm: float, moving: bool, seconds_still: float) -> WifiSignal:
    """Flag irregular breathing or prolonged stillness."""
    reasons: list[str] = []
    score = 0.0
    breathing_anomalous = False
    still_too_long = False

    if bpm > 0 and not (settings.breathing_min_bpm <= bpm <= settings.breathing_max_bpm):
        breathing_anomalous = True
        if bpm < settings.breathing_min_bpm:
            score = max(score, min(1.0, (settings.breathing_min_bpm - bpm) / 8.0))
            reasons.append(f"breathing slow ({bpm:.0f} bpm)")
        else:
            score = max(score, min(1.0, (bpm - settings.breathing_max_bpm) / 15.0))
            reasons.append(f"breathing rapid ({bpm:.0f} bpm)")

    if not moving and seconds_still >= settings.motion_still_seconds:
        still_too_long = True
        score = max(score, min(1.0, seconds_still / 15.0))
        reasons.append(f"stationary {seconds_still:.0f}s")

    flag = breathing_anomalous or still_too_long
    return WifiSignal(
        flag=flag,
        score=score,
        reason="; ".join(reasons) or "normal",
        bpm=bpm,
        moving=moving,
        seconds_still=seconds_still,
        breathing_anomalous=breathing_anomalous,
        still_too_long=still_too_long,
    )
