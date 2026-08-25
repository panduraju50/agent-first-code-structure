from units.codec.impl import b62
from units.validate.impl import validate_url, validate_alias

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

    code = _next_code()
    _db[code] = url
    return code

def _next_code():
    # Keep advancing the sequence until we land on a code that isn't
    # already claimed -- a custom alias can occupy a code that the
    # auto-generator would otherwise have produced later.
    while True:
        _seq[0] += 1
        code = b62(_seq[0])
        if code not in _db:
            return code

def resolve(code):
    return _db.get(code)
