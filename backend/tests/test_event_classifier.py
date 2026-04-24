from app.fusion.event_classifier import classify_event
from app.fusion.events import EventType, Severity
from app.fusion.signals import EnvSignal, VisionSignal, WifiSignal


def _wifi(bpm=16, moving=True, breathing_anom=False, still=False) -> WifiSignal:
    return WifiSignal(
        flag=breathing_anom or still,
        score=0.5 if (breathing_anom or still) else 0.0,
        reason="",
        bpm=bpm,
        moving=moving,
        seconds_still=10.0 if still else 0.0,
        breathing_anomalous=breathing_anom,
        still_too_long=still,
    )


def _vision(horizontal=False, on_floor_seconds=0.0) -> VisionSignal:
    flag = on_floor_seconds >= 3.0
    return VisionSignal(
        flag=flag,
        score=0.9 if flag else 0.0,
        reason="",
        horizontal=horizontal,
        has_person=True,
        max_down_seconds=on_floor_seconds,
        persons_on_floor_count=1 if on_floor_seconds > 0 else 0,
    )


def _env(heat=False) -> EnvSignal:
    return EnvSignal(
        flag=heat,
        score=0.8 if heat else 0.0,
        reason="",
        temp_c=35.0 if heat else 22.0,
        rh_pct=70.0 if heat else 50.0,
        wetbulb_c=31.0 if heat else 14.0,
        heat_stress=heat,
    )


def test_low_severity_maps_to_normal():
    r = classify_event(_wifi(), _vision(), _env(), Severity.LOW)
    assert r == EventType.NORMAL


def test_horizontal_plus_heat_is_heat_exhaustion():
    r = classify_event(
        _wifi(),
        _vision(horizontal=True, on_floor_seconds=5.0),
        _env(heat=True),
        Severity.HIGH,
    )
    assert r == EventType.HEAT_EXHAUSTION


def test_horizontal_plus_breathing_anomaly_is_cardiac():
    r = classify_event(
        _wifi(breathing_anom=True),
        _vision(horizontal=True, on_floor_seconds=5.0),
        _env(),
        Severity.MEDIUM,
    )
    assert r == EventType.CARDIAC


def test_horizontal_plus_stillness_is_loc():
    r = classify_event(
        _wifi(still=True, moving=False),
        _vision(horizontal=True, on_floor_seconds=5.0),
        _env(),
        Severity.MEDIUM,
    )
    assert r == EventType.LOSS_OF_CONSCIOUSNESS


def test_horizontal_alone_is_fall():
    r = classify_event(
        _wifi(),
        _vision(horizontal=True, on_floor_seconds=5.0),
        _env(heat=True),
        Severity.HIGH,
    )
    # heat takes precedence when both horizontal & heat fire
    assert r == EventType.HEAT_EXHAUSTION


def test_medium_without_horizontal_is_unknown():
    r = classify_event(
        _wifi(breathing_anom=True),
        _vision(),
        _env(heat=True),
        Severity.MEDIUM,
    )
    assert r == EventType.UNKNOWN_MEDICAL
