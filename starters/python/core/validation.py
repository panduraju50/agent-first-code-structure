"""Input validators.

This is the ONE home for input-validation rules shared across domains.
`domains.users` and `domains.tasks` both call into this module instead of
writing their own ad-hoc checks.
"""

import re

# Requires at least one char before '@', an '@', and a domain with a dot
# (so "a@b" is rejected but "a@b.com" is accepted).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_title(title: str) -> str:
    """Validate a non-empty title, returning it stripped of surrounding whitespace."""
    if title is None or not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")
    return title.strip()


def validate_email(email: str) -> str:
    """Validate an email address requires an '@' and a dotted domain."""
    if email is None or not isinstance(email, str) or not _EMAIL_RE.match(email.strip()):
        raise ValueError(f"invalid email: {email!r}")
    return email.strip()
