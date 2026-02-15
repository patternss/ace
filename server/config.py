"""
Configuration loading.

Loads server settings from config.yaml and secrets from .env.
Provides a typed configuration object to other modules.

Usage:
    from server.config import get_config

    config = get_config()
    config.server.host  # "0.0.0.0"
    config.server.port  # 8000
    config.llm.provider # "gemini"
    config.llm.api_key  # from .env GEMINI_API_KEY
"""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str


@dataclass(frozen=True)
class Config:
    server: ServerConfig
    llm: LLMConfig


_config: Config | None = None


def load_config() -> Config:
    """Load configuration from config.yaml and .env at the project root.

    Returns:
        A Config instance with all settings populated.

    Raises:
        FileNotFoundError: If config.yaml is missing.
        ValueError: If required environment variables are not set.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    config_path = PROJECT_ROOT / "config.yaml"
    with open(config_path) as f:
        raw = yaml.safe_load(f)

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set. Copy .env.example to .env and add your key."
        )

    return Config(
        server=ServerConfig(
            host=raw["server"]["host"],
            port=raw["server"]["port"],
        ),
        llm=LLMConfig(
            provider=raw["llm"]["provider"],
            model=raw["llm"]["model"],
            api_key=api_key,
        ),
    )


def get_config() -> Config:
    """Get the cached configuration. Loads on first call.

    Returns:
        The Config singleton.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config
