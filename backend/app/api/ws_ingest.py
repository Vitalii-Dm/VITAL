"""WebSocket endpoint where the YOLO pose worker pushes vision events."""
from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ingest.handlers import on_pose_heartbeat, on_pose_snapshot

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ingest/pose")
async def ws_ingest_pose(ws: WebSocket) -> None:
    """Pose worker → backend.

    Expected shapes:

      Snapshot (per stride):
        {
          "zone": "zone-1",
          "timestamp": 1745337600.123,
          "persons": [
            {"track_id": 3, "horizontal": true, "down_seconds": 12.4,
             "bbox": [x1, y1, x2, y2],
             "keypoints": [[x, y, conf], ...17]}
          ]
        }

      Heartbeat (~1 Hz):
        {"type": "heartbeat", "zone": "zone-1", "timestamp": 1745337600.123}
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

    zone_id = str(msg.get("zone", "zone-1"))
    ts_raw = msg.get("timestamp")
    ts = float(ts_raw) if isinstance(ts_raw, (int, float)) else time.time()

    if msg.get("type") == "heartbeat":
        on_pose_heartbeat(zone_id, ts)
        return

    # New multi-person shape.
    if "persons" in msg and isinstance(msg["persons"], list):
        on_pose_snapshot(zone_id, msg["persons"], ts)
        return

    # Tolerate the legacy single-person shape during development so an
    # older pose worker build can still drive the backend. Synthesise a
    # one-person snapshot with no keypoints and zero duration.
    if "horizontal" in msg:
        person = {
            "track_id": 0,
            "horizontal": bool(msg.get("horizontal", False)),
            "down_seconds": 0.0,
            "bbox": [0, 0, 0, 0],
            "keypoints": [],
        }
        on_pose_snapshot(zone_id, [person], ts)
        return

    log.warning("pose ingest: unrecognised message shape keys=%s", list(msg.keys()))
