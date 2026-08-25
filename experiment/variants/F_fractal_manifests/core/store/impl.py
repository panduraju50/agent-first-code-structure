from core.codec.impl import b62
from core.validate.impl import validate_url, validate_alias

_db = {}
_seq = [0]

def shorten(url, alias=None):
    """Shorten a url. If alias is given, use it as the short code instead
    of auto-generating one; raises ValueError if the alias is invalid or
    already taken."""
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
    # avoid clobbering a code that was previously claimed as a custom
    # alias and happens to match the next auto-generated sequence value
    while code in _db:
        _seq[0] += 1
        code = b62(_seq[0])
    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
