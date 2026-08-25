CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62

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
    return isinstance(u, str) and len(u.strip()) > 0

def validate_alias(alias):
    """A custom alias must be a non-empty string made only of base62
    characters, so it stays URL-safe and can't collide in shape with
    the auto-generated codes."""
    return isinstance(alias, str) and len(alias) > 0 and all(c in CHARSET for c in alias)

_db = {}
_seq = [0]

def shorten(url, alias=None):  # impl of S-01
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
    while code in _db:  # don't hand out a code a custom alias already claimed
        _seq[0] += 1
        code = b62(_seq[0])
    _db[code] = url
    return code
