"""Round-trip test: fake_csi.py-format bytes → decoder → expected fields.

We regenerate a v2 frame here (matching `scripts/fake_csi.py`) so that if
either side drifts, this test breaks.
"""
import struct

import numpy as np

from app.ingest.csi_udp import decode


def _build_v2_frame(node_id: int, temp_c: float, rh_pct: float, n_sub: int = 56) -> bytes:
    amp = (np.arange(n_sub, dtype=np.int16) * 10).astype("<i2")
    phase = np.zeros(n_sub, dtype="<i2")
    header = struct.pack(
        "<BBHIHiI",
        2,                 # version
        node_id,
        123,               # seq
        456_000,           # timestamp_ms
        n_sub,
        int(temp_c * 100),
        int(rh_pct * 100),
    )
    return header + amp.tobytes() + phase.tobytes()


def test_decode_v2_frame_roundtrip():
    pkt = _build_v2_frame(node_id=3, temp_c=28.5, rh_pct=62.0)
    frame = decode(pkt)
    assert frame is not None
    assert frame.version == 2
    assert frame.node_id == 3
    assert frame.seq == 123
    assert frame.timestamp_ms == 456_000
    assert frame.amplitude.shape == (56,)
    assert frame.phase.shape == (56,)
    assert abs(frame.temp_c - 28.5) < 1e-3
    assert abs(frame.rh_pct - 62.0) < 1e-3
    # amplitude[5] was set to 50 by the builder
    assert float(frame.amplitude[5]) == 50.0


def test_decode_rejects_truncated_frame():
    assert decode(b"\x02\x01") is None
    assert decode(b"") is None


def test_decode_unknown_version_returns_none():
    # version 0x09 is not recognised → decoder returns None (defensive).
    bogus = b"\x09" + b"\x00" * 50
    assert decode(bogus) is None
