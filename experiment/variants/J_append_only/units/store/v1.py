from units.codec.v1 import b62
from units.validate.v1 import validate_url, validate_alias

_db = {}
_seq = [0]

def shorten(url, alias=None):
    if not validate_url(url):
        raise ValueError("bad url")

    if alias is not None:
        if not validate_alias(alias):
            raise ValueError("invalid alias")
        if alias in _db:
            raise ValueError("alias taken")
        _db[alias] = url
        return alias

    # Auto-generate, skipping any code a custom alias already claimed.
    while True:
        _seq[0] += 1
        code = b62(_seq[0])
        if code not in _db:
            break
    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
