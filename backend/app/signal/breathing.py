"""Breathing-rate extraction from WiFi CSI amplitude.

Ported from ruvnet/RuView `wifi-densepose-vitals/src/breathing.rs`.
Algorithm: per-subcarrier IIR bandpass 0.1-0.5 Hz (human respiration band),
then zero-crossing count on the most energetic subcarrier → breaths/min.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfiltfilt

BREATH_LOW_HZ = 0.1
BREATH_HIGH_HZ = 0.5
WINDOW_SECONDS = 20.0


@dataclass
class BreathingEstimate:
    bpm: float
    confidence: float
    subcarrier_idx: int


class BreathingExtractor:
    """Sliding-window breathing-rate estimator over multi-subcarrier CSI amplitude."""

    def __init__(self, sample_rate_hz: float = 28.0, window_seconds: float = WINDOW_SECONDS):
        self.fs = sample_rate_hz
        self.window = int(sample_rate_hz * window_seconds)
        self._buffer: deque[np.ndarray] = deque(maxlen=self.window)
        self._sos = butter(
            N=4,
            Wn=[BREATH_LOW_HZ, BREATH_HIGH_HZ],
            btype="bandpass",
            fs=sample_rate_hz,
            output="sos",
        )

    def push(self, amplitude: np.ndarray) -> None:
        """Append one CSI frame (shape: [n_subcarriers])."""
        self._buffer.append(np.asarray(amplitude, dtype=np.float32))

    def estimate(self) -> BreathingEstimate | None:
        if len(self._buffer) < int(self.fs * 5):
            return None  # need >=5s of data

        x = np.stack(self._buffer, axis=0)  # [T, N_subcarriers]
        x = x - x.mean(axis=0, keepdims=True)  # remove static component

        filtered = sosfiltfilt(self._sos, x, axis=0)
        energies = np.var(filtered, axis=0)
        best = int(np.argmax(energies))
        signal = filtered[:, best]

        # zero-crossing count → cycles → BPM
        zero_crossings = np.sum(np.diff(np.sign(signal)) != 0)
        cycles = zero_crossings / 2.0
        duration_s = len(signal) / self.fs
        bpm = (cycles / duration_s) * 60.0 if duration_s > 0 else 0.0

        # confidence: SNR-ish — peak energy vs. median
        median_e = float(np.median(energies))
        peak_e = float(energies[best])
        snr = peak_e / max(median_e, 1e-9)
        confidence = float(np.clip((snr - 1.0) / 9.0, 0.0, 1.0))

        return BreathingEstimate(bpm=float(bpm), confidence=confidence, subcarrier_idx=best)
