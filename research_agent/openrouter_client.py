"""Thin wrapper around the OpenRouter API: chat completions, model
listing, and remaining-credit lookups.
"""
from __future__ import annotations

import requests

from research_agent.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL


def _headers() -> dict:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Get one at "
            "https://openrouter.ai/settings/keys and add it to your .env file."
        )
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional, but OpenRouter uses these for attribution on their leaderboards.
        "HTTP-Referer": "https://github.com/your-username/research-agent",
        "X-Title": "AI Research Digest Agent",
    }


def chat_completion(
    messages: list[dict],
    model: str | None = None,
    max_tokens: int = 4000,
    temperature: float = 0.3,
) -> str:
    """Send a chat completion request and return the assistant's text content.

    `model` overrides the default from config for this call only -- pass
    any OpenRouter model slug (e.g. "anthropic/claude-opus-5") to swap
    models per-call without touching the rest of the pipeline.
    """
    payload = {
        "model": model or OPENROUTER_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=_headers(),
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"OpenRouter error: {data['error']}")

    return data["choices"][0]["message"]["content"]


def get_key_usage() -> dict:
    """Return usage info for the configured API key: spend so far and
    remaining limit (both in USD; `limit_remaining` is null if the key
    has no hard cap set).
    """
    response = requests.get(f"{OPENROUTER_BASE_URL}/auth/key", headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json().get("data", {})


def list_models() -> list[dict]:
    """Return the full OpenRouter model catalog: id, name, pricing, context length.

    Useful for building a model picker -- this endpoint needs no auth.
    """
    response = requests.get(f"{OPENROUTER_BASE_URL}/models", timeout=30)
    response.raise_for_status()
    return response.json().get("data", [])


if __name__ == "__main__":
    # Quick manual check: `python -m research_agent.openrouter_client`
    usage = get_key_usage()
    print("OpenRouter key usage:", usage)
