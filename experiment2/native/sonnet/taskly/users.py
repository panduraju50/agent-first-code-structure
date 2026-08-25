"""User accounts, authentication, and sessions.

Owns everything about the ``User`` entity end to end: creation (with
email validation + password hashing), lookup, login (password
verification -> session), and session validation/revocation. Nothing
outside this module touches ``store.users``, ``store.email_index``, or
``store.sessions`` directly.
"""

from . import ids, security
from .dates import utc_now
from .errors import AuthError, ConflictError, NotFoundError
from .models import User
from .store import TasklyStore
from .validation import validate_email, validate_id, validate_password

USER_ID_PREFIX = "usr"


class UserService:
    def __init__(self, store: TasklyStore):
        self._store = store

    def create_user(self, email: str, password: str) -> User:
        """Create a user. Raises ValidationError for a bad email/password,
        ConflictError if the (normalized) email is already registered.
        """
        email = validate_email(email)
        validate_password(password)
        if email in self._store.email_index:
            raise ConflictError(f"a user with email {email!r} already exists")
        user = User(
            id=ids.new_id(USER_ID_PREFIX),
            email=email,
            password_hash=security.hash_password(password),
            created_at=utc_now(),
        )
        self._store.users.save(user.id, user)
        self._store.email_index[email] = user.id
        return user

    def get_user(self, user_id: str) -> User:
        """Look up a user by id. Raises NotFoundError if missing."""
        user_id = validate_id(user_id, "user_id")
        return self._store.users.require(user_id)

    def get_user_by_email(self, email: str) -> User:
        email = validate_email(email)
        user_id = self._store.email_index.get(email)
        if user_id is None:
            raise NotFoundError(f"no user with email {email!r}")
        return self._store.users.require(user_id)

    def authenticate(self, email: str, password: str) -> security.Session:
        """Verify credentials and start a new session.

        Raises AuthError on any credential mismatch (unknown email or
        wrong password) with the *same* message either way, so callers
        (and anyone reading logs) can't distinguish "no such account"
        from "wrong password" — that distinction is a user-enumeration
        leak.
        """
        try:
            user = self.get_user_by_email(email)
        except NotFoundError:
            raise AuthError("invalid email or password")
        if not security.verify_password(password, user.password_hash):
            raise AuthError("invalid email or password")
        return self._create_session(user.id)

    def _create_session(self, user_id: str) -> security.Session:
        token = security.new_session_token()
        now = utc_now().timestamp()
        session = security.Session(
            token=token,
            user_id=user_id,
            created_at=now,
            expires_at=now + security.DEFAULT_SESSION_TTL_SECONDS,
        )
        self._store.sessions[token] = session
        return session

    def get_user_by_session(self, token: str) -> User:
        """Resolve a session token to its user. Raises AuthError if the
        token is unknown or has expired (an expired session is also
        evicted from the store as a side effect).
        """
        session = self._store.sessions.get(token)
        if session is None:
            raise AuthError("invalid session token")
        if session.is_expired():
            del self._store.sessions[token]
            raise AuthError("session token expired")
        return self.get_user(session.user_id)

    def revoke_session(self, token: str) -> None:
        """Log out. Idempotent — revoking an unknown/already-revoked
        token is not an error.
        """
        self._store.sessions.pop(token, None)
