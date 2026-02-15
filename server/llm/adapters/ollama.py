"""
Ollama LLM adapter.

Implements the LLM interface using the ollama Python SDK.
Connects to a local (or remote) Ollama instance.

Usage:
    # Normally instantiated by the router, not directly:
    adapter = OllamaAdapter(model="qwen3-vl:30b")
    response = await adapter.chat(messages)
    async for chunk in adapter.stream(messages):
        print(chunk)
"""

from collections.abc import AsyncGenerator

from ollama import AsyncClient

from server.llm.router import Message


class OllamaAdapter:
    """Adapter for Ollama's local LLM API.

    Converts between the router's Message format and Ollama's
    dict-based message format. Roles are identical ("user",
    "assistant") so conversion is trivial.

    Args:
        model: The Ollama model name (e.g., "qwen3-vl:30b").
        host: Ollama server URL. Empty string uses the SDK default
              (http://localhost:11434).
    """

    def __init__(self, model: str, host: str = "") -> None:
        self.model = model
        self._client = AsyncClient(host=host) if host else AsyncClient()

    async def chat(self, messages: list[Message]) -> str:
        """Send messages to Ollama, return the complete response.

        Args:
            messages: Conversation history in standard format.

        Returns:
            The full response text from Ollama.
        """
        response = await self._client.chat(
            model=self.model,
            messages=self._to_ollama_messages(messages),
        )
        return response.message.content

    async def stream(self, messages: list[Message]) -> AsyncGenerator[str, None]:
        """Send messages to Ollama, yield response text chunks.

        Args:
            messages: Conversation history in standard format.

        Yields:
            Text chunks as they arrive from Ollama.
        """
        response = await self._client.chat(
            model=self.model,
            messages=self._to_ollama_messages(messages),
            stream=True,
        )
        async for part in response:
            if part.message.content:
                yield part.message.content

    @staticmethod
    def _to_ollama_messages(
        messages: list[Message],
    ) -> list[dict[str, str]]:
        """Convert standard messages to Ollama's dict format.

        Args:
            messages: Messages in standard format.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        return [{"role": m.role, "content": m.content} for m in messages]
