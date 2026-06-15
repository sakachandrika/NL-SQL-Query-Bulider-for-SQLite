"""
utils/safety.py — SQL safety guards
"""

import re
import time
from collections import defaultdict, deque


# ── Dangerous keyword blocklist ───────────────────────────────────────────────
BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE",
    "REPLACE", "UPSERT", "MERGE", "ATTACH", "DETACH", "PRAGMA",
    "VACUUM", "REINDEX", "ANALYZE",
]

_BLOCK_PATTERN = re.compile(
    r"\b(" + "|".join(BLOCKED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Multiple statements (semicolons mid-query)
_MULTI_STMT = re.compile(r";.*\S", re.DOTALL)

# Comment injection attempts
_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/|#)", re.IGNORECASE)


class SafetyViolation(Exception):
    """Raised when a query fails a safety check."""


def check_query_safety(sql: str) -> None:
    """
    Raises SafetyViolation if the SQL contains dangerous constructs.
    Otherwise returns None (safe to proceed).
    """
    stripped = sql.strip()

    if not stripped:
        raise SafetyViolation("Empty query.")

    # Must start with SELECT
    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        raise SafetyViolation(
            "Only SELECT queries are allowed. "
            f"Your query starts with: **{stripped.split()[0].upper()}**"
        )

    # Block dangerous keywords anywhere in the query
    found = _BLOCK_PATTERN.findall(stripped)
    if found:
        raise SafetyViolation(
            f"Query contains blocked keyword(s): **{', '.join(set(k.upper() for k in found))}**"
        )

    # Block multi-statement injection
    # Strip the trailing semicolon (allowed) then check for more content
    check_str = stripped.rstrip(";").rstrip()
    if _MULTI_STMT.search(check_str):
        raise SafetyViolation("Multiple SQL statements are not allowed.")

    # Warn on comment injection attempts
    if _COMMENT_PATTERN.search(stripped):
        raise SafetyViolation(
            "SQL comments (-- /* */ #) are not allowed in generated queries."
        )


# ── Rate limiter ──────────────────────────────────────────────────────────────
class RateLimiter:
    """
    Simple in-memory sliding-window rate limiter.
    Allows max `max_calls` per `window_seconds` per key.
    """

    def __init__(self, max_calls: int = 10, window_seconds: int = 60):
        self.max_calls     = max_calls
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Returns (allowed: bool, remaining: int).
        Removes timestamps outside the window, then checks count.
        """
        now    = time.time()
        bucket = self._buckets[key]

        # Evict old entries
        while bucket and bucket[0] < now - self.window_seconds:
            bucket.popleft()

        remaining = self.max_calls - len(bucket)
        if remaining <= 0:
            return False, 0

        bucket.append(now)
        return True, remaining - 1

    def reset(self, key: str) -> None:
        self._buckets.pop(key, None)


# Module-level singleton
rate_limiter = RateLimiter(max_calls=10, window_seconds=60)
