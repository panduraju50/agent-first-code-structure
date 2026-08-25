from slices.shorten.impl import _db

def resolve(code):
    return _db.get(code)
