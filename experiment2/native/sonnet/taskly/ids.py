"""Base62 ID generation.

Single source of truth for how Taskly mints identifiers, so no service
module rolls its own ID scheme. Two flavors are exposed:

- ``new_id(prefix)``   -> long, unguessable, collision-resistant entity id
                          (e.g. "usr_9fK2mQ...") used as primary keys.
- ``new_reference_code`` -> short, human-shareable code (e.g. notification
                          reference codes people might read aloud or paste
                          into a support ticket).

Both are built on ``os.urandom`` (cryptographically strong) rather than
``random``, since IDs double as unguessable tokens in places (e.g. nothing
stops a caller from using a task id as a de-facto capability token).
"""

import os

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(_ALPHABET)

DEFAULT_ID_LENGTH = 16
DEFAULT_REFERENCE_CODE_LENGTH = 6


def _random_base62(length: int) -> str:
    """Return ``length`` base62 characters drawn from CSPRNG bytes.

    Note: ``byte % 62`` has a very slight modulo bias (256 is not a
    multiple of 62), acceptable for opaque IDs/reference codes of this
    size but not something to rely on for e.g. cryptographic keys.
    """
    return "".join(_ALPHABET[b % _BASE] for b in os.urandom(length))


def new_id(prefix: str = "", length: int = DEFAULT_ID_LENGTH) -> str:
    """Generate a random base62 entity id, e.g. new_id("usr") -> "usr_aB3xQ...".

    ``prefix`` should be a short lowercase entity tag (kept consistent per
    entity type across the codebase — see each service module's
    ``*_ID_PREFIX`` constant) so ids are self-describing in logs and debug
    output.
    """
    body = _random_base62(length)
    return f"{prefix}_{body}" if prefix else body


def new_reference_code(length: int = DEFAULT_REFERENCE_CODE_LENGTH) -> str:
    """Generate a short base62 code for human-facing references.

    Uppercased so it reads unambiguously when spoken/typed (still fully
    base62-decodable if callers want to treat it as a compact integer).
    """
    return _random_base62(length).upper()


def encode_base62(n: int) -> str:
    """Encode a non-negative integer as base62. Useful for turning
    monotonic counters/timestamps into compact, sortable-ish strings.
    """
    if n < 0:
        raise ValueError("encode_base62 requires a non-negative integer")
    if n == 0:
        return _ALPHABET[0]
    digits = []
    while n:
        n, rem = divmod(n, _BASE)
        digits.append(_ALPHABET[rem])
    return "".join(reversed(digits))


def decode_base62(s: str) -> int:
    """Inverse of ``encode_base62``."""
    n = 0
    for ch in s:
        idx = _ALPHABET.find(ch)
        if idx < 0:
            raise ValueError(f"invalid base62 character: {ch!r}")
        n = n * _BASE + idx
    return n
