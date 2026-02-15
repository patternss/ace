"""
LLM Router / Abstraction interface.

Provides a unified interface for LLM calls: chat(messages) -> response,
stream(messages) -> chunks. Routes to the configured adapter.
"""
