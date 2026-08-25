"""Comments on tasks.

Owns ``store.comments`` exclusively. Depends on ``UserService`` (author
existence), ``TaskService`` (parent task existence), and optionally a
``NotificationService`` to notify the task's assignee when someone else
comments.
"""

from typing import Optional

from . import ids
from .dates import utc_now
from .models import Comment
from .notifications import NotificationService
from .pagination import Page, paginate
from .store import TasklyStore
from .tasks import TaskService
from .users import UserService
from .validation import validate_id, validate_non_empty_str

COMMENT_ID_PREFIX = "cmt"
MAX_BODY_LENGTH = 4000


class CommentService:
    def __init__(
        self,
        store: TasklyStore,
        users: UserService,
        tasks: TaskService,
        notifications: Optional[NotificationService] = None,
    ):
        self._store = store
        self._users = users
        self._tasks = tasks
        self._notifications = notifications

    def add_comment(self, task_id: str, author_id: str, body: str) -> Comment:
        task = self._tasks.get_task(task_id)
        self._users.get_user(author_id)
        body = validate_non_empty_str(body, "body", max_length=MAX_BODY_LENGTH)
        comment = Comment(
            id=ids.new_id(COMMENT_ID_PREFIX),
            task_id=task_id,
            author_id=author_id,
            body=body,
            created_at=utc_now(),
        )
        self._store.comments.save(comment.id, comment)
        self._notify_new_comment(task, author_id)
        return comment

    def list_comments(self, task_id: str, limit: int = 20, offset: int = 0) -> Page[Comment]:
        """List a task's comments, oldest first (conversation order)."""
        task_id = validate_id(task_id, "task_id")
        self._tasks.get_task(task_id)  # raises NotFoundError if the task doesn't exist
        items = self._store.comments.filter(lambda c: c.task_id == task_id)
        items.sort(key=lambda c: c.created_at)
        return paginate(items, limit=limit, offset=offset)

    def _notify_new_comment(self, task, author_id: str) -> None:
        if self._notifications is None:
            return
        if not task.assignee_id or task.assignee_id == author_id:
            return  # no assignee, or the assignee is commenting on their own task
        self._notifications.create_notification(
            user_id=task.assignee_id,
            kind="new_comment",
            message=f"New comment on task {task.title!r}",
        )
