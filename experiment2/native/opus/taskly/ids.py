"""Base62 id generation and short reference codes. The ONLY place ids are minted.

- `base62_encode` / `base62_decode`: pure integer <-> base62 string.
- `new_id(prefix)`: collision-resistant sortable-ish id, e.g. "tsk_1Ax9...".
- `short_code(n)`: random human-quotable code (used for notification refs).
"""

import os
import time
import threading

ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(ALPHABET)
_INDEX = {c: i for i, c in enumerate(ALPHABET)}

_lock = threading.Lock()
_counter = 0


def base62_encode(num: int) -> str:
    if num < 0:
        raise ValueError("base62_encode requires a non-negative integer")
    if num == 0:
        return ALPHABET[0]
    out = []
    while num:
        num, rem = divmod(num, _BASE)
        out.append(ALPHABET[rem])
    return "".join(reversed(out))


def base62_decode(text: str) -> int:
    num = 0
    for ch in text:
        if ch not in _INDEX:
            raise ValueError(f"invalid base62 character: {ch!r}")
        num = num * _BASE + _INDEX[ch]
    return num


def _next_number() -> int:
    """Monotonic, unique 64-bit-ish number: time_ns high bits + counter + entropy.

    The process-wide counter guarantees uniqueness even within the same
    nanosecond; entropy makes ids non-guessable.
    """
    global _counter
    with _lock:
        _counter = (_counter + 1) & 0xFFFFF  # 20 bits
        counter = _counter
    entropy = int.from_bytes(os.urandom(2), "big")  # 16 bits
    return (time.time_ns() << 36) | (counter << 16) | entropy


def new_id(prefix: str = "") -> str:
    core = base62_encode(_next_number())
    return f"{prefix}_{core}" if prefix else core


def short_code(length: int = 8) -> str:
    """Random uppercase-friendly code, e.g. 'A1B2C3D4'. Used for reference codes."""
    raw = int.from_bytes(os.urandom(length), "big")
    code = base62_encode(raw)
    if len(code) < length:
        code = ALPHABET[0] * (length - len(code)) + code
    return code[:length]
