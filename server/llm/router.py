"""
LLM Router / Abstraction interface.

Provides a unified interface for LLM calls. Routes to the configured
adapter based on config.yaml settings.

Usage:
    from server.llm.router import get_router, Message

    router = get_router()

    # Full response:
    response = await router.chat(messages)

    # Streaming:
    async for chunk in router.stream(messages):
        send_to_client(chunk)

Message format:
    Messages are a list of Message(role, content) dataclasses.
    role is "user" or "assistant". content is a string.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from server.config import LLMConfig


@dataclass(frozen=True)
class Message:
    """A single message in a conversation.

    Args:
        role: "user" or "assistant".
        content: The text content of the message.
    """

    role: str
    content: str


@runtime_checkable
class LLMAdapter(Protocol):
    """Interface that all LLM adapters must satisfy.

    Adapters receive messages in the standard Message format
    and handle conversion to provider-specific formats internally.
    """

    async def chat(self, messages: list[Message]) -> str:
        """Send messages and return the complete response text."""
        ...

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        """Send messages and yield response text chunks."""
        ...


class LLMRouter:
    """Routes LLM calls to the configured adapter.

    Instantiated once via get_router(). Delegates chat() and stream()
    to whichever adapter is configured in config.yaml.
    """

    def __init__(self, adapter: LLMAdapter) -> None:
        self.adapter = adapter

    async def chat(self, messages: list[Message]) -> str:
        """Send messages to the LLM, return complete response."""
        return await self.adapter.chat(messages)

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        """Send messages to the LLM, yield response chunks."""
        async for chunk in self.adapter.stream(messages):
            yield chunk


_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    """Get the cached router. Creates it on first call using config.

    Reads provider from config.yaml, instantiates the matching adapter,
    and wraps it in an LLMRouter.

    Returns:
        The LLMRouter singleton.

    Raises:
        ValueError: If the configured provider is not supported.
    """
    global _router
    if _router is None:
        from server.config import get_config

        config = get_config()
        adapter = _create_adapter(config.llm)
        _router = LLMRouter(adapter)
    return _router


def _create_adapter(llm_config: LLMConfig) -> LLMAdapter:
    """Instantiate the adapter for the configured provider."""
    if llm_config.provider == "ollama":
        from server.llm.adapters.ollama import OllamaAdapter

        return OllamaAdapter(
            model=llm_config.model,
            host=llm_config.host,
        )
    raise ValueError(f"Unknown LLM provider: {llm_config.provider}")
