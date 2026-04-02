"""
WebSocket support for real-time analysis progress updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections for analysis progress."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, repo_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        if repo_id not in self.active_connections:
            self.active_connections[repo_id] = set()
        self.active_connections[repo_id].add(websocket)
        logger.info("WebSocket connected", repo_id=repo_id)
    
    def disconnect(self, websocket: WebSocket, repo_id: str):
        """Remove WebSocket connection."""
        if repo_id in self.active_connections:
            self.active_connections[repo_id].discard(websocket)
            if not self.active_connections[repo_id]:
                del self.active_connections[repo_id]
        logger.info("WebSocket disconnected", repo_id=repo_id)
    
    async def send_progress(self, repo_id: str, message: Dict):
        """Send progress update to all connected clients for a repo."""
        if repo_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[repo_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error("Failed to send WebSocket message", error=str(e))
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[repo_id].discard(conn)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/analysis/{repo_id}")
async def websocket_analysis_progress(websocket: WebSocket, repo_id: str):
    """
    WebSocket endpoint for real-time analysis progress.
    
    Clients connect to receive progress updates for a specific repository analysis.
    """
    await manager.connect(websocket, repo_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "repo_id": repo_id,
            "message": "Connected to analysis progress stream"
        })
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Echo back to confirm connection is alive
                await websocket.send_json({
                    "type": "pong",
                    "message": "Connection alive"
                })
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "message": "Keep-alive ping"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, repo_id)
    except Exception as e:
        logger.error("WebSocket error", repo_id=repo_id, error=str(e))
        manager.disconnect(websocket, repo_id)


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
