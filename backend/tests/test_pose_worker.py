"""Unit tests for the pose-worker posture helpers.

The full worker needs a webcam and a YOLO model to run, but the posture
rule is a pure function over keypoint arrays + bbox. Test it directly so
regressions are caught without the full pipeline.
"""
from __future__ import annotations

import numpy as np

from pose_worker.yolo_runner import (
    POSTURE_ON_FLOOR,
    POSTURE_STANDING,
    POSTURE_UNKNOWN,
    _classify_posture,
    _torso_vertical,
)


def _upright_keypoints() -> tuple[np.ndarray, np.ndarray]:
    """17-keypoint COCO upright pose — shoulders above hips, small dx."""
    xy = np.zeros((17, 2), dtype=float)
    conf = np.zeros(17, dtype=float)
    # shoulders ~y=100, hips ~y=200, dy=100, dx≈0 → strongly vertical.
    xy[5] = [100, 100]  # left_shoulder
    xy[6] = [140, 100]  # right_shoulder
    xy[11] = [100, 200]  # left_hip
    xy[12] = [140, 200]  # right_hip
    for i in (5, 6, 11, 12):
        conf[i] = 0.9
    return xy, conf


def _on_side_keypoints() -> tuple[np.ndarray, np.ndarray]:
    """Person lying on their side — dx >> dy → not vertical."""
    xy = np.zeros((17, 2), dtype=float)
    conf = np.zeros(17, dtype=float)
    xy[5] = [100, 100]
    xy[6] = [100, 140]
    xy[11] = [300, 100]
    xy[12] = [300, 140]
    for i in (5, 6, 11, 12):
        conf[i] = 0.9
    return xy, conf


def _low_conf_keypoints() -> tuple[np.ndarray, np.ndarray]:
    xy, conf = _upright_keypoints()
    conf[11] = 0.1  # left hip below confidence threshold
    return xy, conf


def test_torso_vertical_true_for_upright():
    xy, conf = _upright_keypoints()
    assert _torso_vertical(xy, conf) is True


def test_torso_vertical_false_when_sideways():
    xy, conf = _on_side_keypoints()
    assert _torso_vertical(xy, conf) is False


def test_torso_vertical_rejects_low_confidence():
    xy, conf = _low_conf_keypoints()
    assert _torso_vertical(xy, conf) is False


def test_classify_posture_standing():
    xy, conf = _upright_keypoints()
    # Tall bbox: h=300, w=50 → h/w=6, well above 1.2.
    posture = _classify_posture(
        xy, conf, bbox=(90, 40, 140, 340), on_floor=False, aspect_threshold=1.2
    )
    assert posture == POSTURE_STANDING


def test_classify_posture_on_floor_wins_over_vertical():
    xy, conf = _upright_keypoints()
    # Even if torso looks vertical, an active down_since timer means the
    # debounced on_floor input should dominate.
    posture = _classify_posture(
        xy, conf, bbox=(90, 40, 140, 340), on_floor=True, aspect_threshold=1.2
    )
    assert posture == POSTURE_ON_FLOOR


def test_classify_posture_unknown_when_ambiguous():
    xy, conf = _low_conf_keypoints()
    # Not on floor, torso can't be scored confidently → unknown.
    posture = _classify_posture(
        xy, conf, bbox=(90, 40, 140, 340), on_floor=False, aspect_threshold=1.2
    )
    assert posture == POSTURE_UNKNOWN


def test_classify_posture_unknown_when_bbox_too_short():
    xy, conf = _upright_keypoints()
    # Very wide, short bbox (e.g. crouching / squatting torso occluded) —
    # h/w < threshold means we can't confidently call it standing.
    posture = _classify_posture(
        xy, conf, bbox=(0, 0, 500, 100), on_floor=False, aspect_threshold=1.2
    )
    assert posture == POSTURE_UNKNOWN
