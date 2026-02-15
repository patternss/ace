"""
WebSocket connection handler.

Manages WebSocket connections: accept, receive/parse messages,
dispatch responses, handle disconnections. Does NOT contain
business logic — delegates to the session manager (Phase 0.4+).

For now, echoes user messages back as assistant responses
to prove the WebSocket round-trip works.

Usage:
    # In main.py:
    from server.connection import websocket_endpoint

    @app.websocket("/ws")
    async def ws(websocket: WebSocket):
        await websocket_endpoint(websocket)
"""

import logging

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from server.protocol import (
    AssistantResponseText,
    ConnectionPing,
    ConnectionPong,
    ErrorMessage,
    ErrorPayload,
    ProtocolError,
    TextResponsePayload,
    UserInputText,
    parse_incoming,
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Tracks active WebSocket connections.

    Transport layer only — knows who is connected and how to send them
    messages. Does not manage sessions, state, or business logic.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a WebSocket connection and start tracking it."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info("Client connected (%d active)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Stop tracking a WebSocket connection."""
        self._connections.discard(websocket)
        logger.info("Client disconnected (%d active)", len(self._connections))

    async def send(self, websocket: WebSocket, message: BaseModel) -> None:
        """Serialize and send a message to a single client."""
        await websocket.send_text(message.model_dump_json(by_alias=True))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket handler. Accepts connection, loops receiving messages."""
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = parse_incoming(raw)
            except ProtocolError as e:
                await manager.send(
                    websocket,
                    ErrorMessage(payload=ErrorPayload(code=e.code, message=e.message)),
                )
                continue

            await handle_message(websocket, message)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        logger.exception("Unexpected WebSocket error")
        manager.disconnect(websocket)


async def handle_message(
    websocket: WebSocket, message: UserInputText | ConnectionPing
) -> None:
    """Dispatch a parsed message to the appropriate handler.

    Phase 0.2: echoes user text back. Phase 0.4 will replace this
    with the real orchestration loop.
    """
    if isinstance(message, ConnectionPing):
        await manager.send(websocket, ConnectionPong())
    elif isinstance(message, UserInputText):
        # Placeholder echo — replaced by LLM call in Phase 0.4
        await manager.send(
            websocket,
            AssistantResponseText(
                payload=TextResponsePayload(
                    text=f"Echo: {message.payload.text}",
                    is_partial=False,
                    session_id=message.payload.session_id,
                )
            ),
        )
