from packages.codec.impl import b62
from packages.validate.impl import validate_url, validate_alias

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
        code = alias
    else:
        _seq[0] += 1
        code = b62(_seq[0])
        # An auto-generated code can collide with a custom alias someone
        # already claimed (e.g. alias="1" then seq reaches 1 -> b62 also
        # gives "1"). Skip ahead until we land on an unused code.
        while code in _db:
            _seq[0] += 1
            code = b62(_seq[0])

    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
