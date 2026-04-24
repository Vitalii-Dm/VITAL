#!/usr/bin/env python3
"""Synthetic CSI frame emitter — drives the backend without real ESP32s.

Scenarios:
- normal:                 steady 16 bpm breathing, cool, moving
- breathing-then-collapse: 16 bpm for 45s → rapid (40 bpm) + still + hot after 45s
- hot-zone:               normal breathing but wet-bulb rises above 28°C

Usage::

    python scripts/fake_csi.py --scenario breathing-then-collapse --zone 1
"""
from __future__ import annotations

import argparse
import socket
import struct
import time
from dataclasses import dataclass

import numpy as np

N_SUBCARRIERS = 56
FS = 28.0  # Hz


@dataclass
class Phase:
    bpm: float
    temp_c: float
    rh_pct: float
    moving: bool


def scenario_phases(name: str, elapsed: float) -> Phase:
    if name == "normal":
        return Phase(bpm=16, temp_c=22, rh_pct=50, moving=True)
    if name == "hot-zone":
        return Phase(bpm=16, temp_c=35, rh_pct=70, moving=True)
    if name == "breathing-then-collapse":
        if elapsed < 45:
            return Phase(bpm=16, temp_c=33, rh_pct=65, moving=True)
        return Phase(bpm=42, temp_c=35, rh_pct=72, moving=False)
    raise SystemExit(f"unknown scenario {name}")


def build_frame(node_id: int, seq: int, ts_ms: int, phase: Phase, t: float,
                rng: np.random.Generator) -> bytes:
    hz = phase.bpm / 60.0
    amp = rng.normal(0, 0.3, size=N_SUBCARRIERS).astype(np.float32)
    # Inject breathing on a few subcarriers.
    for idx in (18, 22, 30):
        amp[idx] += 4.0 * np.sin(2 * np.pi * hz * t)
    if phase.moving:
        amp += rng.normal(0, 1.5, size=N_SUBCARRIERS).astype(np.float32)

    amp_i16 = np.clip(amp * 1000, -32000, 32000).astype(np.int16)
    phase_i16 = np.zeros(N_SUBCARRIERS, dtype=np.int16)

    header = struct.pack(
        "<BBHIHiI",
        2,               # version
        node_id,
        seq & 0xFFFF,
        ts_ms & 0xFFFFFFFF,
        N_SUBCARRIERS,
        int(phase.temp_c * 100),
        int(phase.rh_pct * 100),
    )
    return header + amp_i16.tobytes() + phase_i16.tobytes()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="breathing-then-collapse")
    p.add_argument("--zone", type=int, default=1, help="node_id (= zone-{N})")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5005)
    p.add_argument("--duration", type=float, default=120.0)
    args = p.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rng = np.random.default_rng(1337)
    t0 = time.monotonic()
    seq = 0
    dt = 1 / FS

    print(f"[fake_csi] scenario={args.scenario} zone={args.zone} → udp://{args.host}:{args.port}")
    while True:
        elapsed = time.monotonic() - t0
        if elapsed > args.duration:
            break
        phase = scenario_phases(args.scenario, elapsed)
        frame = build_frame(args.zone, seq, int(elapsed * 1000), phase, elapsed, rng)
        sock.sendto(frame, (args.host, args.port))
        seq += 1
        # real-time cadence
        nxt = t0 + seq * dt
        sleep_for = nxt - time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for)


if __name__ == "__main__":
    main()
