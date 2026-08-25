CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62

MIN_ALIAS_LEN = 1
MAX_ALIAS_LEN = 32

def b62(n):
    """Encode a non-negative int to a base62 code."""
    if n == 0:
        return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out
        n //= 62
    return out

def validate_url(u):
    # accept any non-empty string
    return len(u.strip()) > 0

def validate_alias(alias):
    """An alias must be a non-empty string made only of base62 charset
    characters (so it can never be confused with a URL-encoding issue),
    within a sane length range."""
    if not isinstance(alias, str):
        return False
    if not (MIN_ALIAS_LEN <= len(alias) <= MAX_ALIAS_LEN):
        return False
    return all(ch in CHARSET for ch in alias)

_db = {}
_seq = [0]

def shorten(url, alias=None):
    if not validate_url(url):
        raise ValueError("bad url")

    if alias is not None:
        if not validate_alias(alias):
            raise ValueError("invalid alias")
        if alias in _db:
            raise ValueError("alias already taken")
        _db[alias] = url
        return alias

    _seq[0] += 1
    code = b62(_seq[0])
    # An auto-generated code could theoretically collide with a
    # previously-claimed custom alias (e.g. someone claims "b" as an
    # alias before the counter reaches it). Guard against silently
    # overwriting someone's custom mapping.
    while code in _db:
        _seq[0] += 1
        code = b62(_seq[0])
    _db[code] = url
    return code
