"""Base62 id encoding.

This is the ONE home for base62 encode/decode logic in the whole repo.
No other file may define its own base62 alphabet or encoder — the boundary
enforcer (tools/boundary_check.py) fails the build if one shows up elsewhere.
"""

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(_ALPHABET)


def to_base62(n: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("to_base62 requires an int")
    if n < 0:
        raise ValueError("to_base62 requires a non-negative integer")
    if n == 0:
        return _ALPHABET[0]
    digits = []
    while n:
        n, rem = divmod(n, _BASE)
        digits.append(_ALPHABET[rem])
    return "".join(reversed(digits))


def from_base62(s: str) -> int:
    """Decode a base62 string back into an integer."""
    if not s:
        raise ValueError("from_base62 requires a non-empty string")
    n = 0
    for ch in s:
        try:
            idx = _ALPHABET.index(ch)
        except ValueError:
            raise ValueError(f"invalid base62 character: {ch!r}") from None
        n = n * _BASE + idx
    return n


def new_id(seed: int) -> str:
    """Derive a base62 id from a domain-local monotonic counter.

    Domains own their own counters; core only owns the encoding.
    """
    return to_base62(seed)
