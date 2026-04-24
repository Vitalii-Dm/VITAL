#!/usr/bin/env python3
"""Synthetic pose event emitter — mimics the YOLO pose worker.

Usage::

    python scripts/fake_yolo.py --scenario fall-at-45s --zone zone-1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time

import websockets


async def run(backend_ws: str, zone: str, scenario: str, fall_at: float) -> None:
    print(f"[fake_yolo] scenario={scenario} → {backend_ws}")
    async with websockets.connect(backend_ws) as ws:
        t0 = time.monotonic()
        prev_horizontal = False
        while True:
            elapsed = time.monotonic() - t0
            if scenario == "standing":
                horizontal = False
            elif scenario == "fall-at-45s":
                horizontal = elapsed >= fall_at
            elif scenario == "already-down":
                horizontal = True
            else:
                raise SystemExit(f"unknown scenario {scenario}")

            fall_transient = horizontal and not prev_horizontal
            prev_horizontal = horizontal

            await ws.send(
                json.dumps(
                    {
                        "zone": zone,
                        "horizontal": horizontal,
                        "fall_transient": fall_transient,
                        "has_person": True,
                    }
                )
            )
            await asyncio.sleep(0.1)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="fall-at-45s")
    p.add_argument("--zone", default="zone-1")
    p.add_argument("--backend-ws", default="ws://localhost:8000/ws/ingest/pose")
    p.add_argument("--fall-at", type=float, default=45.0)
    args = p.parse_args()
    asyncio.run(run(args.backend_ws, args.zone, args.scenario, args.fall_at))


if __name__ == "__main__":
    main()
