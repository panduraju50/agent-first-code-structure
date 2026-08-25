"""Shared utilities: ID generation, hashing, validation, date formatting."""

import re
import secrets
import string
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
import bcrypt


# Base62 encoding alphabet
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_base62_id(length: int = 12) -> str:
    """Generate a random base62 ID of given length."""
    return ''.join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


def encode_to_base62(num: int) -> str:
    """Convert integer to base62 string."""
    if num == 0:
        return '0'

    digits = []
    while num > 0:
        digits.append(BASE62_ALPHABET[num % 62])
        num //= 62

    return ''.join(reversed(digits))


def decode_base62(s: str) -> int:
    """Convert base62 string to integer."""
    result = 0
    for char in s:
        result = result * 62 + BASE62_ALPHABET.index(char)
    return result


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hash_: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hash_.encode('utf-8'))


def generate_session_token() -> str:
    """Generate a secure session token (base62, 32 chars)."""
    return generate_base62_id(32)


def generate_notification_code() -> str:
    """Generate a short reference code for notifications (6 chars)."""
    return generate_base62_id(6).upper()


def validate_email_address(email: str) -> str:
    """Validate and normalize an email address. Raises ValueError if invalid."""
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError as e:
        raise ValueError(f"Invalid email: {str(e)}")


def validate_string_field(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
    """Validate a string field. Raises ValueError if invalid."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    value = value.strip()

    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} character(s)")

    if len(value) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters")

    return value


def validate_tags(tags: list) -> list:
    """Validate and clean a list of tag strings."""
    if not isinstance(tags, list):
        raise ValueError("Tags must be a list")

    cleaned = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValueError("Each tag must be a string")

        tag = tag.strip().lower()
        if len(tag) > 50:
            raise ValueError("Tag must be at most 50 characters")
        if tag and tag not in cleaned:  # no duplicates, no empty
            cleaned.append(tag)

    return cleaned


def format_datetime(dt: datetime) -> str:
    """Format a datetime object to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat() + 'Z'


def parse_datetime(dt_str: str) -> datetime:
    """Parse an ISO 8601 datetime string to datetime object."""
    if isinstance(dt_str, datetime):
        return dt_str
    # Handle both with and without 'Z'
    dt_str = dt_str.rstrip('Z')
    return datetime.fromisoformat(dt_str)


def get_utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.utcnow()


def validate_pagination(limit: int = 20, offset: int = 0) -> tuple:
    """Validate and constrain pagination parameters."""
    max_limit = 100

    if limit < 1:
        limit = 20
    if limit > max_limit:
        limit = max_limit

    if offset < 0:
        offset = 0

    return limit, offset
