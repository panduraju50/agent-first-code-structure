"""Notifications: create (with a short reference code), list, mark read.

Other services depend on this one to notify users of events (assignment,
completion, comments), so it takes no dependency on them — it sits at the
bottom of the service graph.
"""

from ..models import Notification, to_dict
from ..ids import new_id, short_code
from ..dates import now_iso
from ..pagination import paginate, DEFAULT_PER_PAGE

REF_CODE_LEN = 8


class NotificationService:
    def __init__(self, store):
        self.store = store

    def create(self, user_id: str, kind: str, message: str) -> dict:
        """Create a notification. Caller guarantees user_id exists (internal use)."""
        note = Notification(
            id=new_id("ntf"),
            user_id=user_id,
            kind=kind,
            message=message,
            ref_code=short_code(REF_CODE_LEN),
            read=False,
            created_at=now_iso(),
        )
        self.store.notifications[note.id] = note
        return to_dict(note)

    def list(self, user_id: str, unread_only: bool = False,
             page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        items = [
            n for n in self.store.notifications.values()
            if n.user_id == user_id and (not unread_only or not n.read)
        ]
        items.sort(key=lambda n: n.created_at, reverse=True)  # newest first
        return paginate([to_dict(n) for n in items], page, per_page)

    def mark_read(self, notification_id: str) -> dict:
        note = self.store.get_or_404(self.store.notifications, notification_id, "notification")
        note.read = True
        return to_dict(note)
