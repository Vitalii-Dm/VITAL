import numpy as np

from app.signal.motion import MotionDetector


def test_motion_detects_activity():
    det = MotionDetector(sample_rate_hz=28.0, window_seconds=2.0)
    rng = np.random.default_rng(0)
    for _ in range(28):
        # large random swings → moving
        det.push(rng.normal(0, 5.0, size=56).astype(np.float32))
    state = det.push(rng.normal(0, 5.0, size=56).astype(np.float32))
    assert state.moving is True
    assert state.seconds_still == 0.0


def test_motion_detects_stillness_and_accumulates_seconds_still():
    det = MotionDetector(sample_rate_hz=28.0, window_seconds=2.0)
    # perfectly constant frame → zero diff → still
    frame = np.zeros(56, dtype=np.float32)
    state = None
    for _ in range(30):
        state = det.push(frame, dt=1 / 28.0)
    assert state is not None
    assert state.moving is False
    assert state.seconds_still > 0.5
