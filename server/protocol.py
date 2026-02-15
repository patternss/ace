"""
WebSocket message protocol models.

Defines the JSON message format for client-server communication.
All messages have a 'type' field and a 'payload' field.

Phase 0.2 implements: user.input.text, assistant.response.text,
connection.ping, connection.pong, error.
Full protocol defined in protocol.md at project root.

Usage:
    # Parse an incoming message:
    msg = parse_incoming('{"type": "user.input.text", ...}')

    # Create an outgoing message:
    msg = AssistantResponseText(
        payload=TextResponsePayload(
            text="Hello", is_partial=False, session_id="s1"
        )
    )
    raw = msg.model_dump_json(by_alias=True)
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that converts between camelCase JSON and snake_case Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


# --- Incoming messages (client -> server) ---


class TextInputPayload(CamelModel):
    text: str
    session_id: str


class UserInputText(BaseModel):
    type: Literal["user.input.text"] = "user.input.text"
    payload: TextInputPayload


class ConnectionPing(BaseModel):
    type: Literal["connection.ping"] = "connection.ping"


# --- Outgoing messages (server -> client) ---


class TextResponsePayload(CamelModel):
    text: str
    is_partial: bool
    session_id: str


class AssistantResponseText(BaseModel):
    type: Literal["assistant.response.text"] = "assistant.response.text"
    payload: TextResponsePayload


class ErrorPayload(BaseModel):
    code: str
    message: str
    context: str | None = None


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    payload: ErrorPayload


class ConnectionPong(BaseModel):
    type: Literal["connection.pong"] = "connection.pong"


# --- Message type registry ---

_INCOMING_TYPES: dict[str, type[BaseModel]] = {
    "user.input.text": UserInputText,
    "connection.ping": ConnectionPing,
}


class ProtocolError(Exception):
    """Raised when a message cannot be parsed or has an unknown type."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def parse_incoming(raw: str) -> UserInputText | ConnectionPing:
    """Parse a raw JSON string into a typed incoming message.

    Args:
        raw: JSON string with 'type' and optional 'payload' fields.

    Returns:
        A validated message model instance.

    Raises:
        ProtocolError: If JSON is invalid, type is unknown, or payload fails validation.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ProtocolError("INVALID_MESSAGE", f"Malformed JSON: {e}") from e

    if not isinstance(data, dict) or "type" not in data:
        raise ProtocolError("INVALID_MESSAGE", "Message must have a 'type' field")

    msg_type = data["type"]
    model_class = _INCOMING_TYPES.get(msg_type)
    if model_class is None:
        raise ProtocolError("INVALID_MESSAGE", f"Unknown message type: {msg_type}")

    try:
        return model_class.model_validate(data)
    except Exception as e:
        raise ProtocolError(
            "INVALID_PAYLOAD",
            f"Invalid payload for {msg_type}: {e}",
        ) from e
