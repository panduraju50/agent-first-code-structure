import string

_ALIAS_CHARS = set(string.ascii_letters + string.digits + "-_")
_ALIAS_MIN_LEN = 1
_ALIAS_MAX_LEN = 32


def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0


def validate_alias(alias):
    """Validate a user-supplied custom short code (format only).

    Rules: must be a string, non-empty, within length bounds, made up of
    URL-safe characters (letters, digits, hyphen, underscore), and free of
    leading/trailing whitespace. This does NOT check availability -- that
    depends on what's already stored, which is the store unit's job.
    """
    if not isinstance(alias, str):
        return False
    if alias != alias.strip():
        return False
    if not (_ALIAS_MIN_LEN <= len(alias) <= _ALIAS_MAX_LEN):
        return False
    return all(c in _ALIAS_CHARS for c in alias)
