"""
Session Manager / Orchestration loop.

Owns conversation history and orchestrates LLM calls.
Takes user text in, yields response chunks out.
Has zero WebSocket awareness — the connection layer wraps
chunks in protocol messages.

Usage:
    from server.session_manager import handle_user_message

    async for chunk in handle_user_message("session-1", "Hello"):
        send_chunk_to_client(chunk)
"""

from collections.abc import AsyncGenerator

from server.llm.router import Message, get_router

# In-memory conversation history: session_id → list of messages.
# No persistence — cleared on server restart. Phase 1 adds memory.
_sessions: dict[str, list[Message]] = {}


def get_history(session_id: str) -> list[Message]:
    """Get or create conversation history for a session.

    Args:
        session_id: Client-provided session identifier.

    Returns:
        The message list for this session (mutable reference).
    """
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


async def handle_user_message(session_id: str, text: str) -> AsyncGenerator[str, None]:
    """Process a user message and stream the LLM response.

    Appends the user message to history, streams the response from
    the LLM router, yields each chunk, then appends the complete
    assistant response to history.

    Args:
        session_id: Client-provided session identifier.
        text: The user's message text.

    Yields:
        Response text chunks as they arrive from the LLM.
    """
    history = get_history(session_id)
    history.append(Message(role="user", content=text))

    router = get_router()
    full_text = ""
    async for chunk in router.stream(history):
        full_text += chunk
        yield chunk

    history.append(Message(role="assistant", content=full_text))
