"""Twilio SMS for HIGH-severity alerts. No-op if credentials are unset."""
from __future__ import annotations

import asyncio
import logging

from app.config import settings

log = logging.getLogger(__name__)


async def send_supervisor_sms(body: str) -> None:
    if not (
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
        and settings.supervisor_phone_number
    ):
        log.info("[twilio-disabled] would send: %s", body)
        return

    def _send() -> None:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=body,
            from_=settings.twilio_from_number,
            to=settings.supervisor_phone_number,
        )

    try:
        await asyncio.to_thread(_send)
        log.info("twilio SMS sent")
    except Exception as e:  # noqa: BLE001 — demo-grade error handling
        log.exception("twilio send failed: %s", e)
