"""Environmental layer classifier — heat stress from wet-bulb."""
from __future__ import annotations

from app.config import settings
from app.fusion.signals import EnvSignal


def classify_env(temp_c: float, rh_pct: float, wetbulb_c: float) -> EnvSignal:
    heat_stress = wetbulb_c >= settings.wetbulb_heat_stress_c
    reason = f"wet-bulb {wetbulb_c:.1f}°C"

    if heat_stress:
        excess = wetbulb_c - settings.wetbulb_heat_stress_c
        score = min(1.0, excess / 5.0 + 0.5)
        return EnvSignal(
            flag=True,
            score=score,
            reason=reason,
            temp_c=temp_c,
            rh_pct=rh_pct,
            wetbulb_c=wetbulb_c,
            heat_stress=True,
        )

    return EnvSignal(
        flag=False,
        score=0.0,
        reason=reason,
        temp_c=temp_c,
        rh_pct=rh_pct,
        wetbulb_c=wetbulb_c,
        heat_stress=False,
    )
