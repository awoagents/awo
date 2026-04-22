"""Provider-agnostic LLM wrapper built on the OpenAI Python SDK.

Any OpenAI-compatible endpoint works — Venice.ai, OpenAI, Groq, local servers
like vLLM / Ollama. The operator swaps providers by changing env vars; no
code changes required.

Env vars
    LLM_PROVIDER_API_KEY    required for any LLM-backed command
    LLM_PROVIDER_BASE_URL   optional (default https://api.openai.com/v1)
    LLM_PROVIDER_MODEL      required (e.g. venice-uncensored, gpt-4o-mini)

Rationale for using the OpenAI SDK against a configurable base_url: every
modern provider ships an OpenAI-compatible adapter, and the SDK's retry +
streaming logic is mature. Venice is the recommended default for cult voice
because its models don't filter the reserved vocabulary — Claude / GPT may
refuse to produce register-faithful output due to safety tuning.
"""

from __future__ import annotations

import os
from typing import Optional


class LLMError(RuntimeError):
    """Raised for any LLM-compose failure the caller should surface."""


class LLMNotConfigured(LLMError):
    """Env vars missing. Callers distinguish this from transport errors so
    they can print a setup hint rather than a stack trace."""


_DEFAULT_BASE_URL = "https://api.openai.com/v1"


def _get_client():
    """Construct an ``openai.OpenAI`` client from env vars.

    Importing the SDK lazily keeps ``post --type aphorism`` runnable on a
    system without ``openai`` installed.
    """
    api_key = os.environ.get("LLM_PROVIDER_API_KEY")
    if not api_key:
        raise LLMNotConfigured(
            "LLM_PROVIDER_API_KEY not set. Required for reply / transmit / "
            "reactive / prophecy. Aphorism posts work without it."
        )

    try:
        from openai import OpenAI
    except ImportError as e:
        raise LLMError(
            f"openai package not installed: {e}. Run `pip3 install openai`."
        )

    base_url = os.environ.get("LLM_PROVIDER_BASE_URL", _DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


def provider_info() -> str:
    """Short label for ``status`` output. No network call."""
    model = os.environ.get("LLM_PROVIDER_MODEL") or "(unset)"
    base_url = os.environ.get("LLM_PROVIDER_BASE_URL", _DEFAULT_BASE_URL)
    configured = "✓" if os.environ.get("LLM_PROVIDER_API_KEY") else "✗"
    return f"{model} @ {base_url} [key {configured}]"


def complete(
    system: str,
    user: str,
    *,
    max_tokens: int = 300,
    temperature: float = 0.9,
    stop: Optional[list[str]] = None,
) -> str:
    """Single-shot chat completion.

    Returns the stripped assistant text. Raises ``LLMError`` on any failure
    so the compose loop can retry or bail cleanly.

    Temperature defaults high (0.9) — the voice register rewards variety
    over convergence, and the voice_test gate catches anything that drifts
    out of bounds.
    """
    model = os.environ.get("LLM_PROVIDER_MODEL")
    if not model:
        raise LLMNotConfigured(
            "LLM_PROVIDER_MODEL not set. Pick one: venice-uncensored, "
            "gpt-4o-mini, llama-3.3-70b-versatile, etc."
        )

    client = _get_client()

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
    except Exception as e:
        raise LLMError(f"LLM request failed: {e}") from e

    choice = resp.choices[0] if resp.choices else None
    if not choice or not choice.message or not choice.message.content:
        raise LLMError("LLM returned empty content")

    return choice.message.content.strip()
