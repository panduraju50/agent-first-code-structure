"""Comments: add to a task, list for a task. Notifies interested users."""

from .. import validation
from ..models import Comment, to_dict
from ..ids import new_id
from ..dates import now_iso
from ..pagination import paginate, DEFAULT_PER_PAGE


class CommentService:
    def __init__(self, store, notifications):
        self.store = store
        self.notifications = notifications

    def add(self, task_id: str, author_id: str, body: str) -> dict:
        task = self.store.get_or_404(self.store.tasks, task_id, "task")
        self.store.get_or_404(self.store.users, author_id, "user")
        body = validation.validate_str(body, "body", min_len=1, max_len=2000)

        comment = Comment(
            id=new_id("cmt"),
            task_id=task_id,
            author_id=author_id,
            body=body,
            created_at=now_iso(),
        )
        self.store.comments[comment.id] = comment

        # Notify the task creator and assignee, excluding the comment author.
        for recipient in {task.creator_id, task.assignee_id} - {None, author_id}:
            self.notifications.create(
                recipient, "task_comment", f"New comment on task '{task.title}'"
            )
        return to_dict(comment)

    def list(self, task_id: str, page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        self.store.get_or_404(self.store.tasks, task_id, "task")
        items = [c for c in self.store.comments.values() if c.task_id == task_id]
        items.sort(key=lambda c: c.created_at)
        return paginate([to_dict(c) for c in items], page, per_page)
