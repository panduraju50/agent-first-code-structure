"""Password hashing and session-token primitives.

Password hashing uses PBKDF2-HMAC-SHA256 (stdlib ``hashlib``, no external
dependency) with a random per-password salt, encoded into one
self-describing string so the iteration count can change over time
without invalidating old hashes:

    "pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>"

Session tokens are opaque, cryptographically random strings
(``secrets.token_urlsafe``) with a server-side expiry. Taskly does not
implement JWTs or any self-encoding token format — the token is a bearer
credential that only means something looked up against the session store
(see ``store.TasklyStore.sessions``).
"""

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16

DEFAULT_SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours


def hash_password(password: str) -> str:
    """Hash a plaintext password into a self-describing encoded string.

    Caller is expected to have already run the password through
    ``validation.validate_password``; this function does not itself
    enforce length/type rules.
    """
    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Check a plaintext password against a hash produced by
    ``hash_password``. Returns False (never raises) for a malformed
    ``encoded`` value, so a corrupted stored hash fails closed.
    """
    try:
        algorithm, iterations_s, salt_hex, hash_hex = encoded.split("$")
        if algorithm != _ALGORITHM:
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(expected, actual)


@dataclass
class Session:
    """A live login session. Stored server-side, keyed by ``token``."""

    token: str
    user_id: str
    created_at: float  # unix timestamp (time.time())
    expires_at: float

    def is_expired(self, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else now
        return now >= self.expires_at


def new_session_token() -> str:
    """Generate a new opaque, unguessable session token."""
    return secrets.token_urlsafe(32)
