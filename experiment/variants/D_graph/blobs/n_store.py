from blobs.n_codec import b62
from blobs.n_validate import validate_url, validate_alias

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
    # Auto-generated codes must not collide with a custom alias that was
    # claimed earlier and happens to match a future sequence value (e.g.
    # someone reserves alias "b", which is also b62(11)).
    while code in _db:
        _seq[0] += 1
        code = b62(_seq[0])
    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
