"""
Consciousness Manager (currently: simple recency-based context assembly).

Owns the orchestration loop: persists messages to the database,
assembles recent context for the LLM, streams the response.

Future: this module will grow into the full consciousness model —
multi-source activation (semantic search, facts, temporal patterns),
dynamic space allocation, variable-detail representations. For now
it loads the last N messages by recency.

Usage:
    from server.session_manager import handle_user_message, get_recent_history

    async for chunk in handle_user_message("Hello"):
        send_chunk_to_client(chunk)

    history = await get_recent_history()  # for client display on connect
"""

from collections.abc import AsyncGenerator

from server.config import get_config
from server.database import append_message, get_recent_messages
from server.llm.router import Message, get_router

# Display limit for history sent to client on reconnect.
_DISPLAY_LIMIT = 100


async def handle_user_message(text: str) -> AsyncGenerator[str, None]:
    """Process a user message and stream the LLM response.

    1. Persist the user message
    2. Load recent context (last context_messages from DB)
    3. Stream LLM response, yielding chunks
    4. Persist the complete assistant response

    Args:
        text: The user's message text.

    Yields:
        Response text chunks as they arrive from the LLM.
    """
    await append_message("user", text)

    config = get_config()
    rows = await get_recent_messages(limit=config.llm.context_messages)
    history = [Message(role=role, content=content) for role, content in rows]

    router = get_router()
    full_text = ""
    async for chunk in router.stream(history):
        full_text += chunk
        yield chunk

    await append_message("assistant", full_text)


async def get_recent_history() -> list[Message]:
    """Load recent messages for client display on connect.

    Returns:
        List of Message objects (up to _DISPLAY_LIMIT).
    """
    rows = await get_recent_messages(limit=_DISPLAY_LIMIT)
    return [Message(role=role, content=content) for role, content in rows]
