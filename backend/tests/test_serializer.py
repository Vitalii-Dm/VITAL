import time

from app.fusion.classifiers import classify_env, classify_vision, classify_wifi
from app.fusion.engine import fuse
from app.fusion.serializer import build_fusion_payload
from app.signal.wetbulb import wet_bulb_c
from app.state import ZoneState


def _make_zone(bpm=16.0, temp=22.0, rh=50.0) -> ZoneState:
    z = ZoneState(zone_id="zone-1")
    z.last_bpm = bpm
    z.last_temp_c = temp
    z.last_rh_pct = rh
    z.waveform.extend([0.1, 0.2, 0.3])
    return z


def _fuse_zone(zone: ZoneState):
    wifi = classify_wifi(bpm=zone.last_bpm, moving=True, seconds_still=0)
    any_horiz = any(p.get("horizontal", False) for p in zone.last_persons)
    max_down = max(
        (float(p.get("down_seconds", 0.0)) for p in zone.last_persons),
        default=0.0,
    )
    vision = classify_vision(horizontal=any_horiz, max_down_seconds=max_down)
    env = classify_env(
        zone.last_temp_c, zone.last_rh_pct, wet_bulb_c(zone.last_temp_c, zone.last_rh_pct)
    )
    return fuse(wifi, vision, env)


def test_payload_shape_and_rounding():
    zone = _make_zone(bpm=16.35, temp=22.49, rh=50.12)
    result = _fuse_zone(zone)

    p = build_fusion_payload(zone, result)
    assert p["type"] == "fusion"
    assert p["zone"] == "zone-1"
    assert p["severity"] == "low"
    assert p["event"] == "normal"
    assert p["bpm"] == 16.4         # 1-dp rounded
    assert p["temp_c"] == 22.5
    assert p["rh_pct"] == 50.1
    assert "wetbulb_c" in p
    assert isinstance(p["waveform"], list)
    assert p["waveform"] == [0.1, 0.2, 0.3]
    assert p["flagged_layers"] == []
    # New pose-related fields are present with sensible defaults.
    assert p["persons"] == []
    assert p["max_down_seconds"] == 0.0
    assert p["pose_stale"] is False


def test_payload_includes_persons_passthrough():
    zone = _make_zone()
    zone.last_persons = [
        {
            "track_id": 3,
            "horizontal": True,
            "down_seconds": 12.4,
            "bbox": [0, 0, 10, 30],
            "keypoints": [[1.0, 2.0, 0.9]],
        }
    ]
    result = _fuse_zone(zone)
    p = build_fusion_payload(zone, result)
    assert p["max_down_seconds"] == 12.4
    assert len(p["persons"]) == 1
    person = p["persons"][0]
    assert person["track_id"] == 3
    assert person["horizontal"] is True
    assert person["down_seconds"] == 12.4
    # Serializer strips bbox from the dashboard payload.
    assert "bbox" not in person
    assert person["keypoints"] == [[1.0, 2.0, 0.9]]


def test_payload_pose_stale_flag():
    zone = _make_zone()
    result = _fuse_zone(zone)

    # Never heard a heartbeat → pose_stale must be False (unknown, not stale).
    assert build_fusion_payload(zone, result)["pose_stale"] is False

    # Heartbeat just now → fresh.
    zone.last_pose_heartbeat = time.time()
    assert build_fusion_payload(zone, result)["pose_stale"] is False

    # Heartbeat 5 s ago → stale (threshold is 3 s).
    zone.last_pose_heartbeat = time.time() - 5.0
    assert build_fusion_payload(zone, result)["pose_stale"] is True
