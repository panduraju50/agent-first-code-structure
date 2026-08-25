import re

_ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0


def validate_alias(a):
    """1-32 chars, letters/digits/underscore/hyphen only."""
    if not isinstance(a, str):
        return False
    return bool(_ALIAS_RE.match(a))
