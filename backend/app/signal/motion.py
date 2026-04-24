"""Motion / stillness detection from CSI amplitude variance."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

STILLNESS_THRESHOLD = 0.02  # variance ratio below this = still


@dataclass
class MotionState:
    moving: bool
    magnitude: float  # normalized 0..1+
    seconds_still: float


class MotionDetector:
    def __init__(self, sample_rate_hz: float = 28.0, window_seconds: float = 2.0):
        self.fs = sample_rate_hz
        self.window = int(sample_rate_hz * window_seconds)
        self._buffer: deque[np.ndarray] = deque(maxlen=self.window)
        self._still_since_s: float = 0.0

    def push(self, amplitude: np.ndarray, dt: float = 1 / 28.0) -> MotionState:
        self._buffer.append(np.asarray(amplitude, dtype=np.float32))
        if len(self._buffer) < 4:
            return MotionState(moving=True, magnitude=1.0, seconds_still=0.0)

        x = np.stack(self._buffer, axis=0)
        # High-frequency energy across subcarriers: std of per-sample diff
        diffs = np.diff(x, axis=0)
        magnitude = float(np.mean(np.std(diffs, axis=0)))

        # Normalize vs. a rough baseline — empirically 0.01..1.0 for ESP32 CSI
        norm = magnitude / STILLNESS_THRESHOLD
        moving = norm > 1.0

        if moving:
            self._still_since_s = 0.0
        else:
            self._still_since_s += dt

        return MotionState(
            moving=moving,
            magnitude=float(np.clip(norm, 0.0, 10.0)),
            seconds_still=self._still_since_s,
        )
