"""Shared input-validation primitives.

Every service module funnels raw caller input through these functions
instead of writing ad-hoc checks inline. That keeps validation rules (and
their error messages) defined exactly once. All functions either return a
normalized value or raise ``ValidationError`` — never both a return value
and a silent failure mode.
"""

import re

from .errors import ValidationError

# Deliberately simple RFC-5322-ish check: one "@", a local part, a domain
# with at least one dot. Good enough to reject obvious garbage without
# rejecting valid-but-unusual addresses a strict regex would choke on.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_email(email: str) -> str:
    """Validate and normalize an email address (trimmed, lowercased).

    Raises ValidationError if ``email`` is missing, not a string, too
    long, or does not look like an email address.
    """
    if not isinstance(email, str):
        raise ValidationError("email must be a string")
    email = email.strip()
    if not email:
        raise ValidationError("email is required")
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValidationError(f"email must be at most {MAX_EMAIL_LENGTH} characters")
    if not _EMAIL_RE.match(email):
        raise ValidationError(f"invalid email address: {email!r}")
    return email.lower()


def validate_password(password: str) -> str:
    """Validate a plaintext password's shape before hashing.

    This only checks length/type — it never normalizes (trims/lowers) the
    password, since whitespace and case are significant in a password.
    """
    if not isinstance(password, str):
        raise ValidationError("password must be a string")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError(f"password must be at most {MAX_PASSWORD_LENGTH} characters")
    return password


def validate_non_empty_str(value, field_name: str, max_length=None, min_length=1) -> str:
    """Validate a required string field: right type, trimmed, non-empty,
    within an optional max length. Returns the trimmed value.
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must not be empty")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    return value


def validate_optional_str(value, field_name: str, max_length=None):
    """Validate an optional string field. ``None`` passes through
    unchanged; anything else must be a string within ``max_length`` once
    trimmed. Returns ``None`` or the trimmed value (which may be "").
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    return value


def validate_id(value, field_name: str) -> str:
    """Validate that a value looks like an id reference (non-empty
    string). Used at service boundaries before repository lookups so a
    bad type (None, int, list, ...) fails with ValidationError rather
    than an obscure lookup/attribute error downstream.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a non-empty string id")
    return value
