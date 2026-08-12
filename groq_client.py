"""
=================================================================================
🏄  PERSONA — GROQ LLM ENGINE HELPER MODULE
=================================================================================
Small, framework-agnostic wrapper around the Groq Python SDK. Nothing here
touches `st.*` so it stays unit-testable and reusable outside Streamlit.

Responsibilities:
    - Build a (cached) Groq client from a resolved API key.
    - Stream chat completions token-by-token for a snappy chat UI.
    - Retry transient failures (rate limits, timeouts, 5xx) with exponential
      backoff, and gracefully step down to a smaller/faster fallback model
      if the primary model keeps failing.

This module has zero Gemini dependencies — it is a straight, from-scratch
implementation against the Groq chat-completions API.
=================================================================================
"""

from __future__ import annotations

import random
import time
from typing import Dict, Generator, List, Optional

from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq, RateLimitError

# ---------------------------------------------------------------------------
# 1. CLIENT CONSTRUCTION
# ---------------------------------------------------------------------------
def build_groq_client(api_key: str, timeout_seconds: float = 30.0) -> Groq:
    """
    Construct a Groq SDK client for the given API key.

    A short request timeout is set explicitly so a slow/hung connection
    can't freeze the Streamlit UI indefinitely — callers get a timely
    APITimeoutError that the retry helper below knows how to handle.
    """
    return Groq(api_key=api_key, timeout=timeout_seconds, max_retries=0)


# ---------------------------------------------------------------------------
# 2. RETRY / BACKOFF CONFIG
# ---------------------------------------------------------------------------
_RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError, APITimeoutError, APIStatusError)
_MAX_ATTEMPTS = 4
_BASE_DELAY_SECONDS = 0.75


def _sleep_with_backoff(attempt: int) -> None:
    """Exponential backoff with jitter: 0.75s, 1.5s, 3s, ... plus a splash of jitter."""
    delay = _BASE_DELAY_SECONDS * (2 ** attempt) + random.uniform(0, 0.25)
    time.sleep(delay)


# ---------------------------------------------------------------------------
# 3. STREAMING CHAT COMPLETION (with retry + automatic model fallback)
# ---------------------------------------------------------------------------
def stream_chat_completion(
    client: Groq,
    messages: List[Dict[str, str]],
    primary_model: str,
    fallback_model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Generator[str, None, None]:
    """
    Stream a chat completion token-by-token, yielding text chunks as they
    arrive so the caller (e.g. `st.write_stream`) can render them live.

    Retries transient errors (rate limits, connection hiccups, timeouts,
    5xx server errors) with exponential backoff. If the primary model keeps
    failing and a `fallback_model` was supplied, the last attempt is made
    against that smaller/faster model instead of giving up entirely.

    Raises:
        The last encountered exception if every attempt (including the
        fallback) fails.
    """
    models_to_try = [primary_model]
    if fallback_model and fallback_model != primary_model:
        models_to_try.append(fallback_model)

    last_error: Optional[Exception] = None

    for model_index, model_name in enumerate(models_to_try):
        is_last_model = model_index == len(models_to_try) - 1
        attempts_for_this_model = _MAX_ATTEMPTS if is_last_model else max(1, _MAX_ATTEMPTS // 2)

        for attempt in range(attempts_for_this_model):
            try:
                stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return  # Successful stream — we're done.

            except _RETRYABLE_EXCEPTIONS as exc:
                last_error = exc
                if attempt < attempts_for_this_model - 1:
                    _sleep_with_backoff(attempt)
                    continue
                # Out of retries for this model — fall through to the next
                # model in `models_to_try` (if any), otherwise re-raise below.
                break

    # Every model/attempt combination failed.
    if last_error is not None:
        raise last_error


# ---------------------------------------------------------------------------
# 4. NON-STREAMING CONVENIENCE WRAPPER (used where a single string is needed)
# ---------------------------------------------------------------------------
def get_chat_completion(
    client: Groq,
    messages: List[Dict[str, str]],
    primary_model: str,
    fallback_model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Collects the full streamed response into a single string."""
    return "".join(
        stream_chat_completion(
            client=client,
            messages=messages,
            primary_model=primary_model,
            fallback_model=fallback_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    )
