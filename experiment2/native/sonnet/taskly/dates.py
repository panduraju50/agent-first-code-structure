"""Date/time formatting helpers.

Taskly stores all timestamps as timezone-aware UTC ``datetime`` objects
(see ``utc_now``). Every place that needs to print or parse a timestamp
goes through this module instead of calling ``strftime``/``strptime``
directly, so the wire format only has one definition.
"""

from datetime import datetime, timezone

# Millisecond-precision ISO-8601 in UTC, e.g. "2026-08-26T10:15:30.123Z".
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
HUMAN_FORMAT = "%b %d, %Y %H:%M UTC"


def utc_now() -> datetime:
    """The current time as a timezone-aware UTC datetime. Use this
    everywhere Taskly needs "now" so every timestamp is directly
    comparable without normalization.
    """
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """Coerce a datetime to timezone-aware UTC. Naive datetimes are
    assumed to already be UTC (Taskly never produces naive datetimes
    itself, but callers may hand one in).
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso8601(dt: datetime) -> str:
    """Format a datetime as millisecond-precision ISO-8601 UTC, e.g.
    "2026-08-26T10:15:30.123Z".
    """
    dt = _as_utc(dt)
    return dt.strftime(ISO_FORMAT)[:-3] + "Z"


def from_iso8601(s: str) -> datetime:
    """Parse a string produced by ``to_iso8601`` back into a UTC datetime."""
    if not isinstance(s, str) or not s.endswith("Z"):
        raise ValueError(f"expected an ISO-8601 UTC string ending in 'Z', got {s!r}")
    dt = datetime.strptime(s[:-1], ISO_FORMAT)
    return dt.replace(tzinfo=timezone.utc)


def to_human(dt: datetime) -> str:
    """Format a datetime for display, e.g. "Aug 26, 2026 10:15 UTC"."""
    return _as_utc(dt).strftime(HUMAN_FORMAT)


def relative_from_now(dt: datetime, now: datetime = None) -> str:
    """Format a datetime relative to now, e.g. "3m ago", "2h ago", "5d ago".

    ``now`` defaults to ``utc_now()``; pass it explicitly for deterministic
    tests. Future timestamps (clock skew, scheduled items) report
    "in the future" rather than a nonsensical negative duration.
    """
    now = _as_utc(now) if now is not None else utc_now()
    dt = _as_utc(dt)
    seconds = (now - dt).total_seconds()
    if seconds < 0:
        return "in the future"
    if seconds < 60:
        return "just now"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m ago"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    days = hours / 24
    return f"{int(days)}d ago"
