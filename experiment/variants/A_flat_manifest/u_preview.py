CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXY"  # 61

def encode(n):
    """Encode an int to a short code (used for preview)."""
    if n == 0:
        return CHARSET[0]
    out = ""
    while n > 0:
        out = CHARSET[n % 61] + out
        n //= 61
    return out

def preview(n):
    return "short.ly/" + encode(n)
