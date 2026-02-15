"""
FastAPI application entrypoint.

Starts the coordination server with a WebSocket endpoint.
Run with: uvicorn server.main:app --reload
"""

from fastapi import FastAPI, WebSocket

from server.connection import websocket_endpoint

app = FastAPI(title="ACE Coordination Server")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.websocket("/ws")
async def ws(websocket: WebSocket) -> None:
    """WebSocket endpoint. Delegates to connection handler."""
    await websocket_endpoint(websocket)
