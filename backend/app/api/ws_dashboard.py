"""WebSocket endpoint the supervisor dashboard + worker PWA subscribe to.

The backend fans out `build_fusion_payload()` messages every ~500 ms (see
`app.fusion.loop`). This endpoint is read-only for clients; any inbound
text is discarded so the socket doubles as a keep-alive.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.alerts.broadcaster import broadcaster

router = APIRouter()


@router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket) -> None:
    await broadcaster.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive; ignore content
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.disconnect(ws)
