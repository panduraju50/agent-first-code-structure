from u_codec import CHARSET

def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0

def validate_alias(alias):
    """Validate a user-supplied custom short code.

    Rules: must be a non-empty string, within a reasonable length,
    and built only from the same charset used for auto-generated
    codes (so a custom alias can never collide with future codes
    that use out-of-charset characters, and every alias is safely
    usable in a URL path).
    """
    if not isinstance(alias, str):
        return False
    alias = alias.strip()
    if not (1 <= len(alias) <= 32):
        return False
    return all(ch in CHARSET for ch in alias)
