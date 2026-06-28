import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.config import settings
from app.core.websocket import manager

router = APIRouter()

@router.websocket("/events")
async def websocket_events_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """Secure WebSocket endpoint. Validates JWT and streams live telemetry per organization."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        org_id = payload.get("org_id")
        if not org_id:
            await websocket.close(code=4003)  # Forbidden
            return
    except Exception:
        await websocket.close(code=4003)
        return

    await manager.connect(org_id, websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(org_id, websocket)