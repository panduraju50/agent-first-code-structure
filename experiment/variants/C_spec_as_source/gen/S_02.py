from gen.S_01 import _db

def resolve(code):  # impl of S-02
    return _db.get(code)
