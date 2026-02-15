"""
FastAPI application entrypoint.

Starts the coordination server with a WebSocket endpoint.
In production, also serves the built Svelte client from client/dist/.
Run with: uvicorn server.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

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


# Serve built Svelte client in production.
# Mounted after all routes so /health and /ws are not shadowed.
# Skipped silently if dist/ doesn't exist (dev mode without a build).
client_dist = Path(__file__).resolve().parent.parent / "client" / "dist"
if client_dist.is_dir():
    app.mount("/", StaticFiles(directory=client_dist, html=True), name="static")
