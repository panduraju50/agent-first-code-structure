"""@card
purpose: encode int to base62 id
api: genid(n)->str
tags: ids, genid
effects: []
deps: []
"""

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62
def genid(n):
    if n == 0: return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out; n //= 62
    return out
