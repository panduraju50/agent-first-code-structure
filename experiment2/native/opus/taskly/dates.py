"""Timestamps and date formatting. The ONLY place time is read or formatted.

Canonical storage format is UTC ISO-8601 with a trailing 'Z'
(e.g. '2026-08-26T14:03:07Z'). All models store timestamps in this format.
"""

from datetime import datetime, timezone

_ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    """Current UTC time in canonical ISO format."""
    return datetime.now(timezone.utc).strftime(_ISO_FMT)


def parse_iso(value: str) -> datetime:
    return datetime.strptime(value, _ISO_FMT).replace(tzinfo=timezone.utc)


def format_date(value: str, fmt: str = "%b %d, %Y") -> str:
    """Human-friendly rendering of a canonical ISO string, e.g. 'Aug 26, 2026'."""
    return parse_iso(value).strftime(fmt)
