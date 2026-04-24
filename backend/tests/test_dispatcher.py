"""Verify side-effects are wired correctly on severity transitions."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.alerts.dispatcher import on_severity_change
from app.fusion.engine import FusionResult
from app.fusion.events import EventType, Severity
from app.state import ZoneState


def _result(severity: Severity, event=EventType.HEAT_EXHAUSTION) -> FusionResult:
    return FusionResult(
        severity=severity,
        event=event,
        label="test",
        confidence=0.9,
        flagged_layers=["wifi", "vision", "env"],
        reasons=["a", "b"],
    )


@pytest.mark.asyncio
async def test_high_transition_fires_sms():
    zone = ZoneState(zone_id="zone-1")
    with patch("app.alerts.dispatcher.send_supervisor_sms", new=AsyncMock()) as sms, \
         patch("app.alerts.dispatcher.set_zone_color") as led:
        await on_severity_change(zone, _result(Severity.HIGH), previous=Severity.MEDIUM)
        # dispatcher schedules SMS as a background task — yield the loop once.
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
