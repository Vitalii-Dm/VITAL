"""Welford online mean/variance — used for z-score anomaly scoring.

Ported from ruvnet/RuView `examples/ruview_live.py`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class WelfordStats:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        return self.m2 / self.n if self.n > 1 else 0.0

    @property
    def stddev(self) -> float:
        return math.sqrt(self.variance)

    def zscore(self, x: float) -> float:
        if self.n < 10 or self.stddev < 1e-9:
            return 0.0
        return (x - self.mean) / self.stddev
