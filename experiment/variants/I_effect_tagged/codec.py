# effects: []
CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # 62

def b62(n):
    """Encode a non-negative int to a base62 code."""
    if n == 0:
        return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 62] + out
        n //= 62
    return out
