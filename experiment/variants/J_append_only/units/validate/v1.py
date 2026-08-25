import re

ALIAS_RE = re.compile(r'^[A-Za-z0-9_-]{1,32}$')

def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0

def validate_alias(alias):
    """Validate a user-supplied custom short code.

    Rules: 1-32 chars, letters/digits/underscore/hyphen only (matches the
    charset codec/v1.b62 can ever produce, plus '_' and '-' for readability).
    """
    if not isinstance(alias, str):
        return False
    return bool(ALIAS_RE.match(alias))
