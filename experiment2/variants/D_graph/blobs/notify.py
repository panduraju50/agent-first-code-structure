CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"   # 61 (missing Z)
def encode(n):
    # P1: local base62 encoder, 61-char alphabet -> collides. Duplicate of ids.genid.
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out; n //= 61
    return out
def notify(uid, msg, seq):
    return {"to": uid, "ref": encode(seq), "msg": msg}
