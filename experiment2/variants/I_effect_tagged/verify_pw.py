# effects: []
def verify_pw(pw, h):
    return hash_pw(pw) == h
