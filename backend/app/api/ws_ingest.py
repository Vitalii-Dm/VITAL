"""WebSocket endpoint where the YOLO pose worker pushes vision events."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ingest.handlers import on_vision_event

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ingest/pose")
async def ws_ingest_pose(ws: WebSocket) -> None:
    """Pose worker → backend. Expected message shape::

        {"zone": "zone-1", "horizontal": false, "fall_transient": false}
    """
    await ws.accept()
    log.info("pose worker connected")
    try:
        while True:
            text = await ws.receive_text()
            _handle(text)
    except WebSocketDisconnect:
        log.info("pose worker disconnected")


def _handle(text: str) -> None:
    try:
        msg = json.loads(text)
    except json.JSONDecodeError:
        log.warning("pose ingest: invalid JSON (%d bytes)", len(text))
        return
    on_vision_event(
        zone_id=str(msg.get("zone", "zone-1")),
        horizontal=bool(msg.get("horizontal", False)),
        fall_transient=bool(msg.get("fall_transient", False)),
    )
