"""Verify side-effects are wired correctly on severity transitions."""
from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest

from app.alerts.dispatcher import on_severity_change
from app.fusion.engine import FusionResult
from app.fusion.events import EventType, Severity
from app.state import ZoneState


def _result(
    severity: Severity,
    event=EventType.HEAT_EXHAUSTION,
    emergency_override: bool = False,
    reasons: list[str] | None = None,
) -> FusionResult:
    return FusionResult(
        severity=severity,
        event=event,
        label="test",
        confidence=0.9,
        flagged_layers=["wifi", "vision", "env"],
        reasons=reasons if reasons is not None else ["a", "b"],
        emergency_override=emergency_override,
    )


def _count_emergency(records) -> int:
    return sum(
        1 for rec in records
        if "EMERGENCY_DISPATCH" in rec.getMessage()
    )


@pytest.mark.asyncio
async def test_high_transition_fires_sms():
    zone = ZoneState(zone_id="zone-1")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()) as sms, \
         patch("app.alerts.dispatcher.set_zone_color") as led:
        await on_severity_change(zone, _result(Severity.HIGH), previous=Severity.MEDIUM)
        await asyncio.sleep(0)
        sms.assert_awaited_once()
        led.assert_called_once()


@pytest.mark.asyncio
async def test_high_to_high_does_not_refire_sms():
    zone = ZoneState(zone_id="zone-1")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()) as sms, \
         patch("app.alerts.dispatcher.set_zone_color"):
        await on_severity_change(zone, _result(Severity.HIGH), previous=Severity.HIGH)
        await asyncio.sleep(0)
        sms.assert_not_awaited()


@pytest.mark.asyncio
async def test_low_severity_does_not_send_sms():
    zone = ZoneState(zone_id="zone-1")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()) as sms, \
         patch("app.alerts.dispatcher.set_zone_color") as led:
        await on_severity_change(
            zone, _result(Severity.LOW, EventType.NORMAL), previous=Severity.MEDIUM
        )
        await asyncio.sleep(0)
        sms.assert_not_awaited()
        led.assert_called_once()


@pytest.mark.asyncio
async def test_emergency_dispatch_fires_once_and_debounces(caplog):
    zone = ZoneState(zone_id="zone-1")
    res = _result(
        Severity.HIGH,
        event=EventType.FALL,
        emergency_override=True,
        reasons=["person on floor 22s", "on floor ≥20s"],
    )
    caplog.set_level(logging.WARNING, logger="app.alerts.dispatcher")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()), \
         patch("app.alerts.dispatcher.set_zone_color"):
        await on_severity_change(zone, res, previous=Severity.MEDIUM)
        await asyncio.sleep(0)
        assert _count_emergency(caplog.records) == 1

        # Staying in HIGH — dispatcher must not refire within the cooldown.
        await on_severity_change(zone, res, previous=Severity.HIGH)
        await asyncio.sleep(0)
        assert _count_emergency(caplog.records) == 1


@pytest.mark.asyncio
async def test_emergency_dispatch_skipped_without_override(caplog):
    zone = ZoneState(zone_id="zone-1")
    # HIGH via regular 3-layer fusion, not the on-floor override.
    res = _result(Severity.HIGH, emergency_override=False)
    caplog.set_level(logging.WARNING, logger="app.alerts.dispatcher")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()), \
         patch("app.alerts.dispatcher.set_zone_color"):
        await on_severity_change(zone, res, previous=Severity.MEDIUM)
        await asyncio.sleep(0)
    assert _count_emergency(caplog.records) == 0
