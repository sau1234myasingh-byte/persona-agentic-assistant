"""
=================================================================================
🏄  PERSONA — CONFIGURATION MODULE (v3 — Groq Backend + Auto .env Loading)
=================================================================================
Centralizes every constant the rest of the app depends on: the long-term
memory map, display constants, and — critically — secure, AUTOMATIC API key
loading from a local ".env" file so the user is never nagged for a key that
already exists on disk.

v3 changes:
  - Migrated the LLM backend from Google Gemini to Groq (OpenAI-compatible
    chat-completions API, served on Groq's LPU inference stack).
  - GOOGLE_API_KEY -> GROQ_API_KEY
  - GEMINI_MODEL_NAME -> GROQ_MODEL_NAME (defaults to Llama 3.3 70B Versatile)
  - Added GROQ_FALLBACK_MODEL_NAME + GROQ_REASONING_MODEL_NAME so app.py can
    gracefully step down (or up, for reasoning-heavy prompts) without any
    hardcoded model strings scattered through the codebase.
=================================================================================
"""

# ---------------------------------------------------------------------------
# 1. IMPORTS
# ---------------------------------------------------------------------------
import os
from typing import Optional

# `python-dotenv` reads a local ".env" file and injects its variables into
# the real process environment (os.environ). We call load_dotenv() once,
# at import time, so that ANY module importing config.py after this point
# can rely on os.environ already being populated.
from dotenv import load_dotenv

load_dotenv()  # Looks for a ".env" file in the current working directory.


# ---------------------------------------------------------------------------
# 2. APP DISPLAY CONSTANTS
# ---------------------------------------------------------------------------
APP_DISPLAY_NAME: str = os.environ.get(
    "APP_DISPLAY_NAME", "Persona Agentic Assistant"
)
APP_PAGE_ICON: str = "🏄"

# ---------------------------------------------------------------------------
# 2b. GROQ MODEL SELECTION
#     Primary   -> fast + high quality general-purpose chat model.
#     Fallback  -> ultra-low-latency, smaller model (rate-limit / outage
#                  fallback, or when the user explicitly wants max speed).
#     Reasoning -> distilled reasoning model, used when a prompt needs
#                  chain-of-thought-style reasoning (long/complex questions).
# ---------------------------------------------------------------------------
GROQ_MODEL_NAME: str = os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
GROQ_FALLBACK_MODEL_NAME: str = os.environ.get(
    "GROQ_FALLBACK_MODEL_NAME", "llama-3.1-8b-instant"
)
GROQ_REASONING_MODEL_NAME: str = os.environ.get(
    "GROQ_REASONING_MODEL_NAME", "deepseek-r1-distill-llama-70b"
)


# ---------------------------------------------------------------------------
# 3. LONG-TERM MEMORY MAPPING
# ---------------------------------------------------------------------------
MEMORY_MAPPING: dict[str, str] = {
    "team": "team@persona.com",
    "captain": "captain@persona.com",
    "coach": "instructor@ai.com",
    "client": "partner@enterprise.com",
}


# ---------------------------------------------------------------------------
# 4. AUTOMATIC API KEY DETECTION
#    This is computed ONCE at import time. If a key is present in the
#    environment (i.e. it was set in ".env"), we capture it immediately so
#    the frontend never has to ask the user for it.
# ---------------------------------------------------------------------------
_ENV_API_KEY: str = os.environ.get("GROQ_API_KEY", "").strip()

# A simple boolean flag the frontend can check WITHOUT needing to know
# anything about how/where the key was resolved from.
ENV_KEY_DETECTED: bool = bool(_ENV_API_KEY)


def resolve_api_key(session_input: Optional[str] = None) -> Optional[str]:
    """
    Resolve the active Groq API key.

    Priority order:
      1. The key auto-detected from the ".env" file at startup (preferred —
         this is what eliminates the sidebar nag entirely).
      2. Whatever the user manually typed into the sidebar this session
         (only relevant as a fallback when no ".env" key exists).
      3. None — no key available anywhere.

    Args:
        session_input: A key the user may have typed into the sidebar.
            Only used if no ".env" key was found.

    Returns:
        The resolved API key string, or None if unavailable.
    """
    # 1. The .env-detected key always wins — it means the developer already
    #    configured this properly, so we never want to override it or ask
    #    the user to redo work that's already done.
    if ENV_KEY_DETECTED:
        return _ENV_API_KEY

    # 2. Fall back to whatever was typed into the sidebar this session.
    if session_input and session_input.strip():
        return session_input.strip()

    # 3. Nothing available.
    return None


def is_llm_engine_active(session_input: Optional[str] = None) -> bool:
    """Convenience boolean check used by the frontend to gate LLM features."""
    return resolve_api_key(session_input) is not None
