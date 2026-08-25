from blobs.n_codec import CHARSET

MAX_ALIAS_LEN = 32


def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0


def validate_alias(alias):
    """Reject a custom alias that is empty, too long, or contains any
    character outside the base62 charset used for auto-generated codes
    (keeps custom and auto-generated codes in the same namespace/format)."""
    if not isinstance(alias, str):
        return False
    if not (0 < len(alias) <= MAX_ALIAS_LEN):
        return False
    return all(c in CHARSET for c in alias)
