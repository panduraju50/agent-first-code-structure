"""Tasks: create, list (filtered), complete, assign, search.

Depends on TagService (tag resolution) and NotificationService (assignment /
completion notices) — both injected, so this module never re-implements their
rules.
"""

from .. import validation
from ..models import Task, TASK_STATUSES, to_dict
from ..ids import new_id
from ..dates import now_iso
from ..pagination import paginate, DEFAULT_PER_PAGE


class TaskService:
    def __init__(self, store, tags, notifications):
        self.store = store
        self.tags = tags
        self.notifications = notifications

    def create(self, project_id: str, creator_id: str, title: str,
               description: str = "", assignee_id: str = None, tag_ids=None) -> dict:
        self.store.get_or_404(self.store.projects, project_id, "project")
        self.store.get_or_404(self.store.users, creator_id, "user")
        title = validation.validate_str(title, "title", min_len=1, max_len=200)
        description = validation.validate_str(description or "", "description", max_len=5000)
        resolved_tags = self.tags.resolve_ids(project_id, tag_ids)
        if assignee_id is not None:
            self.store.get_or_404(self.store.users, assignee_id, "user")

        task = Task(
            id=new_id("tsk"),
            project_id=project_id,
            title=title,
            description=description,
            status="open",
            creator_id=creator_id,
            assignee_id=assignee_id,
            tag_ids=resolved_tags,
            created_at=now_iso(),
            completed_at=None,
        )
        self.store.tasks[task.id] = task
        self._notify_assignment(task, actor_id=creator_id)
        return to_dict(task)

    def list(self, project_id: str = None, status: str = None, assignee_id: str = None,
             page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        if status is not None:
            validation.one_of(status, "status", TASK_STATUSES)
        items = [t for t in self.store.tasks.values() if self._matches(t, project_id, status, assignee_id)]
        items.sort(key=lambda t: t.created_at)
        return paginate([to_dict(t) for t in items], page, per_page)

    def complete(self, task_id: str) -> dict:
        task = self.store.get_or_404(self.store.tasks, task_id, "task")
        if task.status != "done":
            task.status = "done"
            task.completed_at = now_iso()
            # Tell the creator, unless they completed their own task.
            if task.assignee_id and task.assignee_id != task.creator_id:
                self.notifications.create(
                    task.creator_id, "task_completed", f"Task '{task.title}' was completed"
                )
        return to_dict(task)

    def assign(self, task_id: str, assignee_id: str) -> dict:
        task = self.store.get_or_404(self.store.tasks, task_id, "task")
        self.store.get_or_404(self.store.users, assignee_id, "user")
        if task.assignee_id != assignee_id:
            task.assignee_id = assignee_id
            self._notify_assignment(task, actor_id=None)
        return to_dict(task)

    def search(self, query: str, project_id: str = None,
               page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        query = validation.validate_str(query, "query", min_len=1)
        needle = query.lower()
        items = [
            t for t in self.store.tasks.values()
            if (project_id is None or t.project_id == project_id)
            and (needle in t.title.lower() or needle in t.description.lower())
        ]
        items.sort(key=lambda t: t.created_at)
        return paginate([to_dict(t) for t in items], page, per_page)

    # -- internals ---------------------------------------------------------

    @staticmethod
    def _matches(task, project_id, status, assignee_id) -> bool:
        return (
            (project_id is None or task.project_id == project_id)
            and (status is None or task.status == status)
            and (assignee_id is None or task.assignee_id == assignee_id)
        )

    def _notify_assignment(self, task, actor_id) -> None:
        """Notify the assignee, unless they are the one doing the assigning."""
        if task.assignee_id and task.assignee_id != actor_id:
            self.notifications.create(
                task.assignee_id, "task_assigned", f"You were assigned task '{task.title}'"
            )
