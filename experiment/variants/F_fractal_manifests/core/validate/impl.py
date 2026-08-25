def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0

ALIAS_CHARSET = set(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
)
ALIAS_MIN_LEN = 1
ALIAS_MAX_LEN = 32

def validate_alias(alias):
    """Validate a user-supplied custom short code.

    Rules: non-empty string, reasonable length, and restricted to a
    URL-safe charset (alnum plus '-' and '_') so it can't collide with
    reserved path characters or be used to smuggle in odd input.
    """
    if not isinstance(alias, str):
        return False
    if not (ALIAS_MIN_LEN <= len(alias) <= ALIAS_MAX_LEN):
        return False
    return all(c in ALIAS_CHARSET for c in alias)
