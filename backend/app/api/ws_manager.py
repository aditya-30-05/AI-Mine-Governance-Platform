"""WebSocket connection manager for real-time dashboard updates."""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from datetime import datetime

logger = logging.getLogger(__name__)

ws_router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections grouped by mine_id."""

    def __init__(self):
        # All connections: ws -> mine_id
        self.active_connections: Dict[WebSocket, str] = {}
        # mine_id -> set of ws connections
        self.mine_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, mine_id: str = "global"):
        await websocket.accept()
        self.active_connections[websocket] = mine_id
        if mine_id not in self.mine_connections:
            self.mine_connections[mine_id] = set()
        self.mine_connections[mine_id].add(websocket)
        logger.info(f"WS connected: mine={mine_id}, total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        mine_id = self.active_connections.pop(websocket, None)
        if mine_id and mine_id in self.mine_connections:
            self.mine_connections[mine_id].discard(websocket)

    async def send_to_mine(self, mine_id: str, message: dict):
        """Send message to all connections for a specific mine."""
        dead = set()
        connections = self.mine_connections.get(mine_id, set()) | self.mine_connections.get("global", set())
        for ws in connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients."""
        dead = set()
        for ws in list(self.active_connections.keys()):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()


@ws_router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket, mine_id: str = "global"):
    """WebSocket endpoint for dashboard real-time updates."""
    await ws_manager.connect(websocket, mine_id)
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "mine_id": mine_id,
            "timestamp": datetime.utcnow().isoformat(),
        }))

        while True:
            # Keep connection alive — receive pings from client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WS disconnected")


@ws_router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """WebSocket endpoint for critical alerts."""
    await ws_manager.connect(websocket, "alerts")
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "channel": "alerts",
            "timestamp": datetime.utcnow().isoformat(),
        }))
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
