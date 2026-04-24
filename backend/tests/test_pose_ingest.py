"""Tests for the pose-ingest handler path and multi-person timer fusion."""
from __future__ import annotations

import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch

import pytest

from app.alerts.dispatcher import on_severity_change
from app.fusion.events import Severity
from app.fusion.serializer import build_fusion_payload
from app.fusion.zone_fuser import fuse_zone
from app.ingest.handlers import on_pose_heartbeat, on_pose_snapshot
from app.state import ZoneState


def _person(track_id: int, horizontal: bool, down_seconds: float) -> dict:
    return {
        "track_id": track_id,
        "horizontal": horizontal,
        "down_seconds": down_seconds,
        "bbox": [0, 0, 10, 20],
        "keypoints": [[0.0, 0.0, 0.0]] * 17,
    }


def test_on_pose_snapshot_stores_on_zone():
    from app.state import world
    zone_id = "zone-snapshot-test"
    on_pose_snapshot(zone_id, [_person(7, True, 4.0)], ts=12345.0)
    zone = world.zone(zone_id)
    assert len(zone.last_persons) == 1
    assert zone.last_persons[0]["track_id"] == 7
    assert zone.updated_at == 12345.0


def test_fuse_single_person_5s_is_medium_or_lower():
    zone = ZoneState(zone_id="zone-1")
    zone.last_persons = [_person(1, True, 5.0)]
    r = fuse_zone(zone)
    # Only vision flags at 5 s → LOW in the flag-count ladder.
    assert r.severity == Severity.LOW
    assert r.emergency_override is False


def test_fuse_single_person_15s_still_low_without_other_layers():
    zone = ZoneState(zone_id="zone-1")
    zone.last_persons = [_person(1, True, 15.0)]
    r = fuse_zone(zone)
    # Vision alone flagged → LOW by count; emergency override not yet triggered.
    assert r.severity == Severity.LOW
    assert r.emergency_override is False
    # But the vision score has climbed.
    payload = build_fusion_payload(zone, r)
    assert payload["max_down_seconds"] == 15.0


def test_fuse_single_person_25s_forces_high_via_override():
    zone = ZoneState(zone_id="zone-1")
    zone.last_persons = [_person(1, True, 25.0)]
    r = fuse_zone(zone)
    assert r.severity == Severity.HIGH
    assert r.emergency_override is True


@pytest.mark.asyncio
async def test_emergency_dispatch_fires_exactly_once_through_pipeline(caplog):
    """End-to-end-ish: same zone, moving from 5 s → 15 s → 25 s on floor."""
    zone = ZoneState(zone_id="zone-1")
    caplog.set_level(logging.WARNING, logger="app.alerts.dispatcher")

    emergency_messages = lambda: [  # noqa: E731
        rec for rec in caplog.records if "EMERGENCY_DISPATCH" in rec.getMessage()
    ]

    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()), \
         patch("app.alerts.dispatcher.set_zone_color"):
        # 5 s on floor → LOW, no emergency.
        zone.last_persons = [_person(1, True, 5.0)]
        r = fuse_zone(zone)
        await on_severity_change(zone, r, previous=Severity.LOW)
        await asyncio.sleep(0)
        assert r.severity == Severity.LOW
        assert len(emergency_messages()) == 0

        # 15 s on floor → still LOW (vision-alone), no emergency.
        zone.last_persons = [_person(1, True, 15.0)]
        r = fuse_zone(zone)
        await on_severity_change(zone, r, previous=Severity.LOW)
        await asyncio.sleep(0)
        assert len(emergency_messages()) == 0

        # 25 s on floor → HIGH via override, emergency fires ONCE.
        zone.last_persons = [_person(1, True, 25.0)]
        r = fuse_zone(zone)
        await on_severity_change(zone, r, previous=Severity.LOW)
        await asyncio.sleep(0)
        assert r.severity == Severity.HIGH
        assert r.emergency_override is True
        assert len(emergency_messages()) == 1

        # Another tick while still down — must not refire within cooldown.
        zone.last_persons = [_person(1, True, 27.0)]
        r = fuse_zone(zone)
        await on_severity_change(zone, r, previous=Severity.HIGH)
        await asyncio.sleep(0)
        assert len(emergency_messages()) == 1


def test_multiple_tracks_have_independent_timers():
    zone = ZoneState(zone_id="zone-1")
    # Track 1 briefly on floor, track 2 on floor a long time.
    zone.last_persons = [
        _person(1, True, 2.0),
        _person(2, True, 25.0),
    ]
    r = fuse_zone(zone)
    payload = build_fusion_payload(zone, r)
    # max_down_seconds is per-zone max across tracks.
    assert payload["max_down_seconds"] == 25.0
    assert r.severity == Severity.HIGH
    assert r.emergency_override is True

    # Now track 2 is up, track 1 briefly down — no emergency.
    zone2 = ZoneState(zone_id="zone-2")
    zone2.last_persons = [
        _person(1, True, 2.0),
        _person(2, False, 0.0),
    ]
    r2 = fuse_zone(zone2)
    assert r2.severity == Severity.LOW
    assert r2.emergency_override is False


def test_heartbeat_freshness_flag():
    zone = ZoneState(zone_id="zone-1")
    zone.last_persons = [_person(1, False, 0.0)]
    r = fuse_zone(zone)

    # Never got a heartbeat → pose_stale false (unknown, not stale).
    assert build_fusion_payload(zone, r)["pose_stale"] is False

    # Got one right now.
    on_pose_heartbeat(zone.zone_id, time.time())
    # on_pose_heartbeat touches the shared world; pull the same zone for realism.
    from app.state import world
    fresh_zone = world.zone(zone.zone_id)
    fresh_zone.last_persons = zone.last_persons
    r = fuse_zone(fresh_zone)
    assert build_fusion_payload(fresh_zone, r)["pose_stale"] is False

    # Heartbeat aged past the 3 s threshold.
    fresh_zone.last_pose_heartbeat = time.time() - 5.0
    assert build_fusion_payload(fresh_zone, r)["pose_stale"] is True
