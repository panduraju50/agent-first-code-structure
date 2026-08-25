from impl.codec_impl import b62
from impl.validate_impl import validate_url, validate_alias

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
        # auto-generated codes share the same namespace as custom aliases,
        # so skip any sequence value a custom alias already claimed
        while code in _db:
            _seq[0] += 1
            code = b62(_seq[0])

    _db[code] = url
    return code

def resolve(code):
    return _db.get(code)
