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
    s = classify_vision(horizontal=False, fall_transient=False)
    assert s.flag is False


def test_vision_horizontal_flags_high_score():
    s = classify_vision(horizontal=True, fall_transient=False)
    assert s.flag is True
    assert s.horizontal is True
    assert s.score >= 0.8


def test_vision_fall_transient_alone_is_medium_score():
    s = classify_vision(horizontal=False, fall_transient=True)
    assert s.flag is True
    assert s.fall_transient is True
    assert 0.4 < s.score < 0.8


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
