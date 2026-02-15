"""
FastAPI application entrypoint.

Starts the coordination server with a WebSocket endpoint.
Run with: uvicorn server.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="ACE Coordination Server")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
