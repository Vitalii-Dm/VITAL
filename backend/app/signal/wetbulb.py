"""Wet-bulb temperature via Stull 2011 empirical formula.

Stull, R. (2011). "Wet-Bulb Temperature from Relative Humidity and Air
Temperature." J. Appl. Meteorol. Climatol.
"""
from __future__ import annotations

import math


def wet_bulb_c(temp_c: float, rh_pct: float) -> float:
    """Stull 2011. Valid for T in [-20, 50] °C and RH in [5, 99] %."""
    t = temp_c
    r = rh_pct
    return (
        t * math.atan(0.151977 * math.sqrt(r + 8.313659))
        + math.atan(t + r)
        - math.atan(r - 1.676331)
        + 0.00391838 * (r ** 1.5) * math.atan(0.023101 * r)
        - 4.686035
    )


def heat_stress_level(wbt_c: float) -> str:
    """Four-step classification aligned with OSHA heat-stress guidance."""
    if wbt_c < 25:
        return "safe"
    if wbt_c < 28:
        return "elevated"
    if wbt_c < 32:
        return "high"
    return "extreme"
