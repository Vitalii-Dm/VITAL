"""Async loop that runs fusion on every zone at a fixed cadence.

One responsibility only: tick, fuse, broadcast, notify the alert dispatcher.
Side-effects (SMS, LED, logging) live in `alerts/dispatcher.py`.
"""
from __future__ import annotations

import asyncio
import logging

from app.alerts.broadcaster import broadcaster
from app.alerts.dispatcher import on_severity_change
from app.fusion.events import Severity
from app.fusion.serializer import build_fusion_payload
from app.fusion.zone_fuser import fuse_zone
from app.state import world

log = logging.getLogger(__name__)

FUSION_INTERVAL_S = 0.5


async def fusion_loop(interval_s: float = FUSION_INTERVAL_S) -> None:
    log.info("fusion loop started (interval=%.2fs)", interval_s)
    last_severity: dict[str, Severity] = {}
    try:
        while True:
            await asyncio.sleep(interval_s)
            await _tick(last_severity)
    except asyncio.CancelledError:
        log.info("fusion loop cancelled")
        raise


async def _tick(last_severity: dict[str, Severity]) -> None:
    for zone in world.all_zones():
        result = fuse_zone(zone)
        zone.last_fusion = result

        payload = build_fusion_payload(zone, result)
        await broadcaster.broadcast(payload)

        prev = last_severity.get(zone.zone_id, Severity.LOW)
        last_severity[zone.zone_id] = result.severity
        if prev != result.severity:
            await on_severity_change(zone, result, previous=prev)
