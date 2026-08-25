"""User accounts: create/get, login (email+password -> session), session auth.

Owns email validation (via validation module), password hashing (via security
module), and session issuance. Passwords never leave here in plaintext and are
never serialized (models.to_dict strips the hash).
"""

from .. import validation
from ..errors import AuthError, ConflictError
from ..models import User, Session, to_dict
from ..ids import new_id
from ..security import hash_password, verify_password, new_session_token
from ..dates import now_iso


class UserService:
    def __init__(self, store):
        self.store = store

    def create(self, email: str, name: str, password: str) -> dict:
        email = validation.validate_email(email)
        name = validation.validate_str(name, "name", min_len=1, max_len=120)
        validation.validate_password(password)

        if self._find_by_email(email) is not None:
            raise ConflictError(f"email already registered: {email}")

        user = User(
            id=new_id("usr"),
            email=email,
            name=name,
            password_hash=hash_password(password),
            created_at=now_iso(),
        )
        self.store.users[user.id] = user
        return to_dict(user)

    def get(self, user_id: str) -> dict:
        return to_dict(self.store.get_or_404(self.store.users, user_id, "user"))

    def login(self, email: str, password: str) -> dict:
        # Normalize (not full-validate) so a malformed stored-vs-input compare
        # still runs and returns the same generic AuthError.
        email = validation.normalize_email(email)
        user = self._find_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("invalid email or password")

        session = Session(token=new_session_token(), user_id=user.id, created_at=now_iso())
        self.store.sessions[session.token] = session
        return {"token": session.token, "user": to_dict(user)}

    def authenticate(self, token: str) -> dict:
        """Resolve a session token to its user, or raise AuthError."""
        session = self.store.sessions.get(token)
        if session is None:
            raise AuthError("invalid or expired session token")
        return to_dict(self.store.users[session.user_id])

    def logout(self, token: str) -> None:
        self.store.sessions.pop(token, None)

    def _find_by_email(self, normalized_email: str):
        return next((u for u in self.store.users.values() if u.email == normalized_email), None)
