"""Notifications, each with a short human-shareable reference code.

This module owns ``store.notifications`` exclusively. Other services
(``tasks.py`` on assignment, ``comments.py`` on a new comment) are handed
a ``NotificationService`` instance in their constructor and call
``create_notification`` on it rather than writing to the notifications
repository themselves — see ``api.TasklyAPI`` for construction order.
"""

from . import ids
from .dates import utc_now
from .errors import NotFoundError
from .models import Notification
from .pagination import Page, paginate
from .store import TasklyStore
from .users import UserService
from .validation import validate_id, validate_non_empty_str

NOTIFICATION_ID_PREFIX = "ntf"
REFERENCE_CODE_LENGTH = 6
MAX_KIND_LENGTH = 60
MAX_MESSAGE_LENGTH = 500
_MAX_REFERENCE_CODE_ATTEMPTS = 10


class NotificationService:
    def __init__(self, store: TasklyStore, users: UserService):
        self._store = store
        self._users = users

    def create_notification(self, user_id: str, kind: str, message: str) -> Notification:
        self._users.get_user(user_id)
        kind = validate_non_empty_str(kind, "kind", max_length=MAX_KIND_LENGTH)
        message = validate_non_empty_str(message, "message", max_length=MAX_MESSAGE_LENGTH)
        notification = Notification(
            id=ids.new_id(NOTIFICATION_ID_PREFIX),
            user_id=user_id,
            reference_code=self._unique_reference_code(),
            kind=kind,
            message=message,
            created_at=utc_now(),
        )
        self._store.notifications.save(notification.id, notification)
        return notification

    def _unique_reference_code(self) -> str:
        """Mint a reference code guaranteed unique among *existing*
        notifications. Collisions are astronomically unlikely at 6
        base62 chars (~5.6e10 possibilities) but are checked explicitly
        rather than assumed away, since a reused reference code would
        let one notification's code resolve to the wrong entity.
        """
        existing_codes = {n.reference_code for n in self._store.notifications.all()}
        for _ in range(_MAX_REFERENCE_CODE_ATTEMPTS):
            code = ids.new_reference_code(REFERENCE_CODE_LENGTH)
            if code not in existing_codes:
                return code
        # Practically unreachable; widen the code space rather than loop forever.
        return ids.new_reference_code(REFERENCE_CODE_LENGTH + 4)

    def get_by_reference_code(self, reference_code: str) -> Notification:
        reference_code = validate_non_empty_str(reference_code, "reference_code", max_length=32)
        reference_code = reference_code.upper()
        for notification in self._store.notifications.all():
            if notification.reference_code == reference_code:
                return notification
        raise NotFoundError(f"no notification with reference code {reference_code!r}")

    def list_notifications(
        self, user_id: str, unread_only: bool = False, limit: int = 20, offset: int = 0
    ) -> Page[Notification]:
        """List a user's notifications, newest first."""
        user_id = validate_id(user_id, "user_id")
        items = self._store.notifications.filter(lambda n: n.user_id == user_id)
        if unread_only:
            items = [n for n in items if not n.read]
        items.sort(key=lambda n: n.created_at, reverse=True)
        return paginate(items, limit=limit, offset=offset)

    def mark_read(self, notification_id: str) -> Notification:
        notification_id = validate_id(notification_id, "notification_id")
        notification = self._store.notifications.require(notification_id)
        notification.read = True
        return notification
