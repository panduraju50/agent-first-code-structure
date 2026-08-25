def hash_pw(pw):
    return "h$" + str(sum(ord(c) for c in pw))


def verify_pw(pw, h):
    return hash_pw(pw) == h


def make_token(uid):
    return "t-" + str(uid)


def check_token(tok):
    return int(tok[2:]) if tok.startswith("t-") else None
