"""Integration-style tests over the combined fusion → event pipeline."""
from app.fusion.classifiers import classify_env, classify_vision, classify_wifi
from app.fusion.engine import fuse
from app.fusion.events import EventType, Severity
from app.signal.wetbulb import wet_bulb_c


def test_normal_conditions_are_low():
    wifi = classify_wifi(bpm=16, moving=True, seconds_still=0)
    vision = classify_vision(horizontal=False, fall_transient=False)
    env = classify_env(22, 50, wet_bulb_c(22, 50))
    r = fuse(wifi, vision, env)
    assert r.severity == Severity.LOW
    assert r.event == EventType.NORMAL
    assert r.flagged_layers == []


def test_three_layers_agree_triggers_high_heat_exhaustion():
    wifi = classify_wifi(bpm=45, moving=False, seconds_still=10)
    vision = classify_vision(horizontal=True, fall_transient=True)
    env = classify_env(35, 70, wet_bulb_c(35, 70))
    r = fuse(wifi, vision, env)
    assert r.severity == Severity.HIGH
    assert r.event == EventType.HEAT_EXHAUSTION
    assert set(r.flagged_layers) == {"wifi", "vision", "env"}


def test_two_layers_is_medium_loc():
    # wifi (still too long) + vision (horizontal), cool zone.
    wifi = classify_wifi(bpm=16, moving=False, seconds_still=10)
    vision = classify_vision(horizontal=True, fall_transient=False)
    env = classify_env(22, 50, wet_bulb_c(22, 50))
    r = fuse(wifi, vision, env)
    assert r.severity == Severity.MEDIUM
    assert r.event == EventType.LOSS_OF_CONSCIOUSNESS


def test_transient_fall_only_is_low():
    wifi = classify_wifi(bpm=16, moving=True, seconds_still=0)
    vision = classify_vision(horizontal=False, fall_transient=True)
    env = classify_env(22, 50, wet_bulb_c(22, 50))
    r = fuse(wifi, vision, env)
    assert r.severity == Severity.LOW
    assert r.event == EventType.NORMAL
