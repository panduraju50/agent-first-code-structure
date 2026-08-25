"""Input validation. The ONLY place validation rules live.

Every function returns the cleaned value (trimmed/normalized) or raises
`ValidationError`. Services call these instead of hand-rolling checks so a rule
change happens in exactly one spot.
"""

import re

from .errors import ValidationError

# Pragmatic email check: one @, non-empty local part, a dotted domain.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LEN = 8


def require(value, field: str):
    """Reject None and empty/whitespace-only values. Returns the value unchanged."""
    if value is None:
        raise ValidationError(f"{field} is required")
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field} is required")
    return value


def validate_str(value, field: str, min_len: int = 0, max_len: int = 10_000) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    trimmed = value.strip()
    if len(trimmed) < min_len:
        raise ValidationError(f"{field} must be at least {min_len} character(s)")
    if len(trimmed) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} character(s)")
    return trimmed


def normalize_email(value) -> str:
    """Lowercase + trim only. Use for lookups where format was already checked."""
    if not isinstance(value, str):
        raise ValidationError("email must be a string")
    return value.strip().lower()


def validate_email(value) -> str:
    email = normalize_email(value)
    require(email, "email")
    if not _EMAIL_RE.match(email):
        raise ValidationError(f"invalid email address: {value!r}")
    return email


def validate_password(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("password must be a string")
    if len(value) < MIN_PASSWORD_LEN:
        raise ValidationError(f"password must be at least {MIN_PASSWORD_LEN} characters")
    return value


def validate_int(value, field: str, min_value=None, max_value=None) -> int:
    """Coerce to int (bools rejected) and range-check."""
    if isinstance(value, bool) or not isinstance(value, int):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field} must be an integer")
    if min_value is not None and value < min_value:
        raise ValidationError(f"{field} must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field} must be <= {max_value}")
    return value


def one_of(value, field: str, choices):
    if value not in choices:
        raise ValidationError(f"{field} must be one of {sorted(choices)}")
    return value
