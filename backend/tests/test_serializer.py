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


def test_payload_shape_and_rounding():
    zone = _make_zone(bpm=16.35, temp=22.49, rh=50.12)
    wifi = classify_wifi(bpm=zone.last_bpm, moving=True, seconds_still=0)
    vision = classify_vision(horizontal=False, fall_transient=False)
    env = classify_env(zone.last_temp_c, zone.last_rh_pct,
                       wet_bulb_c(zone.last_temp_c, zone.last_rh_pct))
    result = fuse(wifi, vision, env)

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
