"""Thin wrapper around the Anthropic SDK with prompt caching.

Reads ANTHROPIC_API_KEY from .env. Default model = claude-sonnet-4-6.
"""
from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT / ".env")

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


_client: Anthropic | None = None


def get_client() -> Anthropic:
    global _client
    if _client is not None:
        return _client
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill in the key."
        )
    _client = Anthropic(api_key=key)
    return _client


def chat(messages: list[dict],
         system: str | list[dict] | None = None,
         tools: list[dict] | None = None,
         model: str = DEFAULT_MODEL,
         max_tokens: int = 1024,
         temperature: float = 0.0):
    """Single chat call. `system` may be a plain string or a list of content blocks
    (for prompt caching, pass a list with {'type':'text','text':..., 'cache_control':{'type':'ephemeral'}}).
    """
    client = get_client()
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system is not None:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools
    return client.messages.create(**kwargs)


def cached_system(text: str) -> list[dict]:
    """Wrap a system prompt so it qualifies for prompt caching (>=1024 tokens recommended)."""
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
