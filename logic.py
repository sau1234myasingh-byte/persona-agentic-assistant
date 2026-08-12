"""
=================================================================================
🏄  PERSONA — CORE BACKEND LOGIC MODULE
=================================================================================
This module contains pure, testable business logic with zero Streamlit
dependencies. Nothing here touches `st.*` — that separation means these
functions can be unit-tested in isolation and reused in a future CLI, API,
or background worker without dragging the whole frontend along with them.

Functions:
    - sort_reminders(reminders_list)   -> splits reminders into Missed/Future
    - resolve_nickname(text_query, ..) -> parses chat text for a known nickname
=================================================================================
"""

# ---------------------------------------------------------------------------
# 1. IMPORTS
# ---------------------------------------------------------------------------
import datetime
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 2. CUSTOM EXCEPTIONS
#    Defining our own exception type makes error handling explicit and
#    intention-revealing at call sites, instead of catching a generic
#    `Exception` or `KeyError`.
# ---------------------------------------------------------------------------
class NicknameNotFoundError(Exception):
    """
    Raised when `resolve_nickname()` cannot find any known nickname inside
    the supplied text query. Callers should catch this specifically and
    show a friendly fallback message rather than letting it propagate.
    """

    def __init__(self, text_query: str):
        self.text_query = text_query
        super().__init__(
            f"No known nickname could be resolved from the query: {text_query!r}"
        )


# ---------------------------------------------------------------------------
# 3. REMINDER TYPE ALIAS
#    A reminder is expected to be a dictionary shaped like:
#        {
#            "id": int,
#            "task": str,
#            "timestamp": datetime.datetime,
#            "status": "active" | "trashed",
#        }
# ---------------------------------------------------------------------------
Reminder = Dict[str, Any]


# ---------------------------------------------------------------------------
# 4. REMINDER SORTING ENGINE
# ---------------------------------------------------------------------------
def sort_reminders(
    reminders_list: List[Reminder],
    reference_time: Optional[datetime.datetime] = None,
) -> Tuple[List[Reminder], List[Reminder]]:
    """
    Split a list of reminders into two chronologically-sorted buckets:
    Missed (timestamp <= now) and Future (timestamp > now).

    Only reminders whose `status` is `"active"` are considered — anything
    trashed is silently excluded from both buckets.

    Args:
        reminders_list: The full list of reminder dictionaries to evaluate.
        reference_time: The "current time" to compare against. Defaults to
            `datetime.datetime.now()` if not supplied. Exposing this as a
            parameter (rather than hardcoding `datetime.now()` inline) makes
            the function trivially unit-testable with a fixed clock.

    Returns:
        A tuple of (missed_reminders, future_reminders), each sorted in
        ascending chronological order.
    """
    # Default to the live wall-clock time if no reference time was given.
    if reference_time is None:
        reference_time = datetime.datetime.now()

    missed_reminders: List[Reminder] = []
    future_reminders: List[Reminder] = []

    for reminder in reminders_list:
        # Skip anything that has been trashed — it belongs in neither bucket.
        if reminder.get("status") != "active":
            continue

        timestamp = reminder.get("timestamp")

        # Defensive guard: if a reminder is somehow missing a timestamp,
        # skip it rather than crashing the whole sorting pass.
        if not isinstance(timestamp, datetime.datetime):
            continue

        if timestamp <= reference_time:
            missed_reminders.append(reminder)
        else:
            future_reminders.append(reminder)

    # Sort both buckets chronologically (earliest first) for a clean,
    # predictable dashboard reading order.
    missed_reminders.sort(key=lambda r: r["timestamp"])
    future_reminders.sort(key=lambda r: r["timestamp"])

    return missed_reminders, future_reminders


# ---------------------------------------------------------------------------
# 5. NICKNAME RESOLUTION PARSER
# ---------------------------------------------------------------------------
def resolve_nickname(text_query: str, memory_dict: Dict[str, str]) -> str:
    """
    Case-insensitively scan `text_query` for the first known nickname found
    in `memory_dict`, and return its mapped email address.

    Args:
        text_query: The raw user-submitted chat text to search.
        memory_dict: A mapping of nickname -> email address (typically
            `config.MEMORY_MAPPING`).

    Returns:
        The resolved email address string for the first nickname match
        found in the text.

    Raises:
        NicknameNotFoundError: If no nickname key from `memory_dict` appears
            anywhere in `text_query`.
    """
    if not text_query:
        raise NicknameNotFoundError(text_query)

    lowered_query = text_query.lower()

    # Iterate in insertion order so behavior is deterministic and matches
    # the order nicknames were defined in config.py.
    for nickname, email in memory_dict.items():
        if nickname.lower() in lowered_query:
            return email

    # No nickname matched anywhere in the query — raise our custom exception
    # so the caller (the chat handler in app.py) can catch it explicitly and
    # show a friendly fallback message instead of crashing.
    raise NicknameNotFoundError(text_query)