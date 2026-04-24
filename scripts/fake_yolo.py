#!/usr/bin/env python3
"""Synthetic pose event emitter — mimics the YOLO pose worker.

Usage::

    python scripts/fake_yolo.py --scenario down-then-emergency --zone zone-1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time

import websockets

SCENARIOS = ("standing", "fall-at-45s", "already-down", "down-then-emergency")

# Minimal 17-keypoint placeholder — (x, y, conf). Good enough for the wire
# contract tests; real pose worker fills in true pixel coords.
_EMPTY_KP = [[0.0, 0.0, 0.0] for _ in range(17)]


def _person(
    track_id: int,
    horizontal: bool,
    down_seconds: float,
    bbox=(100, 100, 200, 300),
    keypoints=None,
) -> dict:
    return {
        "track_id": track_id,
        "horizontal": bool(horizontal),
        "down_seconds": float(down_seconds),
        "bbox": list(bbox),
        "keypoints": keypoints if keypoints is not None else _EMPTY_KP,
    }


async def run(
    backend_ws: str, zone: str, scenario: str, fall_at: float
) -> None:
    print(f"[fake_yolo] scenario={scenario} → {backend_ws}")
    if scenario not in SCENARIOS:
        raise SystemExit(f"unknown scenario {scenario}; choose from {SCENARIOS}")

    async with websockets.connect(backend_ws) as ws:
        t0 = time.monotonic()
        down_since: float | None = None
        last_heartbeat = 0.0

        while True:
            now_mono = time.monotonic()
            elapsed = now_mono - t0
            now_wall = time.time()

            persons: list[dict] = []

            if scenario == "standing":
                persons.append(_person(1, horizontal=False, down_seconds=0.0))

            elif scenario == "fall-at-45s":
                horiz = elapsed >= fall_at
                if horiz and down_since is None:
                    down_since = now_mono
                elif not horiz:
                    down_since = None
                ds = (now_mono - down_since) if down_since is not None else 0.0
                persons.append(_person(1, horizontal=horiz, down_seconds=ds))

            elif scenario == "already-down":
                if down_since is None:
                    down_since = t0
                ds = now_mono - down_since
                persons.append(_person(1, horizontal=True, down_seconds=ds))

            elif scenario == "down-then-emergency":
                # Standing for 5 s, then on floor counting up for 25 s.
                if elapsed < 5.0:
                    persons.append(_person(1, horizontal=False, down_seconds=0.0))
                    down_since = None
                else:
                    if down_since is None:
                        down_since = now_mono
                    ds = now_mono - down_since
                    persons.append(_person(1, horizontal=True, down_seconds=ds))
                    if ds > 25.0:
                        print("[fake_yolo] 25 s on floor — emergency should have fired")

            await ws.send(
                json.dumps(
                    {
                        "zone": zone,
                        "timestamp": now_wall,
                        "persons": persons,
                    }
                )
            )

            # ~1 Hz heartbeat.
            if now_mono - last_heartbeat >= 1.0:
                await ws.send(
                    json.dumps(
                        {"type": "heartbeat", "zone": zone, "timestamp": now_wall}
                    )
                )
                last_heartbeat = now_mono

            await asyncio.sleep(0.1)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="down-then-emergency", choices=SCENARIOS)
    p.add_argument("--zone", default="zone-1")
    p.add_argument("--backend-ws", default="ws://localhost:8000/ws/ingest/pose")
    p.add_argument("--fall-at", type=float, default=45.0)
    args = p.parse_args()
    asyncio.run(run(args.backend_ws, args.zone, args.scenario, args.fall_at))


if __name__ == "__main__":
    main()
