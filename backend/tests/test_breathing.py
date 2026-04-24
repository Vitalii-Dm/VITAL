"""Synthetic breathing signal → expected BPM within tolerance.

Pattern adapted from ruvnet/RuView `v1/tests/unit/test_sensing.py`.
"""
import numpy as np

from app.signal.breathing import BreathingExtractor


def test_breathing_detects_18bpm():
    fs = 28.0
    duration_s = 25.0
    t = np.arange(0, duration_s, 1 / fs)
    bpm_target = 18.0
    hz = bpm_target / 60.0  # 0.3 Hz

    extractor = BreathingExtractor(sample_rate_hz=fs)
    rng = np.random.default_rng(42)
    n_sub = 56

    for ti in t:
        # Subcarrier 20 carries the signal; rest are noise.
        amp = rng.normal(0, 0.2, size=n_sub).astype(np.float32)
        amp[20] += 5.0 * np.sin(2 * np.pi * hz * ti)
        extractor.push(amp)

    est = extractor.estimate()
    assert est is not None
    assert abs(est.bpm - bpm_target) < 2.0, f"expected ~{bpm_target}, got {est.bpm:.2f}"
    assert est.subcarrier_idx == 20
    assert est.confidence > 0.2


def test_breathing_returns_none_before_warmup():
    fs = 28.0
    extractor = BreathingExtractor(sample_rate_hz=fs)
    for _ in range(10):
        extractor.push(np.zeros(56, dtype=np.float32))
    assert extractor.estimate() is None
