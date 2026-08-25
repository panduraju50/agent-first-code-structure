from u_codec import b62
from u_validate import validate_url, validate_alias

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

    # auto-generate, skipping any code already claimed by a custom alias
    while True:
        _seq[0] += 1
        code = b62(_seq[0])
        if code not in _db:
            _db[code] = url
            return code

def resolve(code):
    return _db.get(code)
