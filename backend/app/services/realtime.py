import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, organization_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(organization_id, set()).add(websocket)

    def disconnect(self, organization_id: str, websocket: WebSocket) -> None:
        self._connections.get(organization_id, set()).discard(websocket)

    async def broadcast_event(self, organization_id: str, payload: dict[str, Any]) -> None:
        payload = {"type": "event", "at": datetime.utcnow().isoformat(), **payload}
        message = json.dumps(payload, default=str)
        stale: list[WebSocket] = []
        for socket in self._connections.get(organization_id, set()):
            try:
                await socket.send_text(message)
            except RuntimeError:
                stale.append(socket)
        for socket in stale:
            self.disconnect(organization_id, socket)


realtime_manager = RealtimeManager()
