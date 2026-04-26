"""
src/api/websocket
WebSocket real-time layer for the BID API (Phase 2).

Exposes:
  ConnectionManager  — per-project connection registry and broadcast helper
  get_manager        — returns the application singleton ConnectionManager
  set_manager        — registers the singleton (called from FastAPI lifespan)
  router             — FastAPI APIRouter with the WS endpoint
"""
from src.api.websocket.manager import ConnectionManager, get_manager, set_manager
from src.api.websocket.router import router

__all__ = ["ConnectionManager", "get_manager", "set_manager", "router"]
