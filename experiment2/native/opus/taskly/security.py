"""Password hashing and session tokens. The ONLY place crypto happens.

Password policy (min length) lives in `validation.validate_password`; this
module assumes the value already passed policy and just hashes/verifies it.
"""

import hashlib
import hmac
import secrets

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 120_000


def hash_password(password: str, *, salt: str = None, iterations: int = _ITERATIONS) -> str:
    """Return an encoded string 'pbkdf2_sha256$iterations$salt$hash'."""
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return f"{_ALGO}${iterations}${salt}${dk.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time check of `password` against an encoded hash."""
    try:
        algo, iterations, salt, expected = encoded.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(dk.hex(), expected)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)
