"""users domain service.

Depends on core (id encoding + email validation) only. Must never import
domains.tasks — the boundary enforcer fails the build if it does.
"""

from core.ids import new_id
from core.validation import validate_email
from domains.users.models import User


class UserStore:
    """In-memory user store: create/get."""

    def __init__(self):
        self._users = {}
        self._counter = 0

    def create(self, email: str) -> User:
        email = validate_email(email)
        self._counter += 1
        user_id = new_id(self._counter)
        user = User(id=user_id, email=email)
        self._users[user_id] = user
        return user

    def get(self, user_id: str) -> User:
        try:
            return self._users[user_id]
        except KeyError:
            raise KeyError(f"no such user: {user_id}") from None
