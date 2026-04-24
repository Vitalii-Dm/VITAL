"""Tests for each per-layer classifier in isolation."""
from app.fusion.classifiers import classify_env, classify_vision, classify_wifi
from app.signal.wetbulb import wet_bulb_c


# ----- wifi -----


def test_wifi_normal_breathing_no_flag():
    s = classify_wifi(bpm=16, moving=True, seconds_still=0.0)
    assert s.flag is False
    assert s.breathing_anomalous is False
    assert s.still_too_long is False


def test_wifi_rapid_breathing_flags():
    s = classify_wifi(bpm=45, moving=True, seconds_still=0.0)
    assert s.flag is True
    assert s.breathing_anomalous is True
    assert "rapid" in s.reason


def test_wifi_slow_breathing_flags():
    s = classify_wifi(bpm=4, moving=True, seconds_still=0.0)
    assert s.flag is True
    assert s.breathing_anomalous is True
    assert "slow" in s.reason


def test_wifi_stillness_flags_after_threshold():
    s = classify_wifi(bpm=16, moving=False, seconds_still=10.0)
    assert s.flag is True
    assert s.still_too_long is True


def test_wifi_short_stillness_does_not_flag():
    s = classify_wifi(bpm=16, moving=False, seconds_still=1.0)
    assert s.flag is False


# ----- vision -----


def test_vision_upright_does_not_flag():
    s = classify_vision(horizontal=False, max_down_seconds=0.0)
    assert s.flag is False
    assert s.score == 0.0


def test_vision_brief_on_floor_does_not_flag():
    # 2 s on floor — below the 3 s threshold.
    s = classify_vision(horizontal=True, max_down_seconds=2.0)
    assert s.flag is False
    assert s.score == 0.0


def test_vision_on_floor_3s_flags_low_score():
    s = classify_vision(horizontal=True, max_down_seconds=5.0)
    assert s.flag is True
    assert s.score == 0.4
    assert "on floor" in s.reason


def test_vision_on_floor_10s_medium_score():
    s = classify_vision(horizontal=True, max_down_seconds=15.0)
    assert s.flag is True
    assert s.score == 0.7


def test_vision_on_floor_20s_top_score():
    s = classify_vision(horizontal=True, max_down_seconds=25.0)
    assert s.flag is True
    assert s.score == 1.0


def test_vision_carries_standing_count():
    s = classify_vision(
        horizontal=False, max_down_seconds=0.0, standing_count=3
    )
    assert s.standing_count == 3
    # Standing alone must not flag — informational only.
    assert s.flag is False
    assert s.score == 0.0


# ----- env -----


def test_env_cool_does_not_flag():
    s = classify_env(22, 50, wet_bulb_c(22, 50))
    assert s.flag is False
    assert s.heat_stress is False


def test_env_hot_flags_heat_stress():
    wbt = wet_bulb_c(35, 70)
    s = classify_env(35, 70, wbt)
    assert s.flag is True
    assert s.heat_stress is True
    assert s.wetbulb_c == wbt
