def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0


def validate_alias(alias):
    """Validate a user-supplied custom short code.

    Must be a non-empty string, of reasonable length, containing only
    URL-safe characters (letters, digits, hyphen, underscore).
    """
    if not isinstance(alias, str):
        return False
    if not (1 <= len(alias) <= 32):
        return False
    return all(c.isalnum() or c in "-_" for c in alias)
