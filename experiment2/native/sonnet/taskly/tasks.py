"""Tasks: create, list, complete, assign, tag, search.

Owns ``store.tasks`` exclusively. Depends on ``UserService`` (existence
checks for creator/assignee), ``ProjectService`` (existence check for the
parent project), ``TagService`` (resolving tag names to tag ids), and
optionally a ``NotificationService`` to fire a notification when a task
gets an assignee.
"""

from typing import Iterable, Optional

from . import ids
from .dates import utc_now
from .models import Task, TaskStatus
from .notifications import NotificationService
from .pagination import Page, paginate
from .projects import ProjectService
from .store import TasklyStore
from .tags import TagService
from .users import UserService
from .validation import validate_id, validate_non_empty_str, validate_optional_str

TASK_ID_PREFIX = "tsk"
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 4000
MAX_SEARCH_QUERY_LENGTH = 200


class TaskService:
    def __init__(
        self,
        store: TasklyStore,
        users: UserService,
        projects: ProjectService,
        tags: TagService,
        notifications: Optional[NotificationService] = None,
    ):
        self._store = store
        self._users = users
        self._projects = projects
        self._tags = tags
        self._notifications = notifications

    def create_task(
        self,
        project_id: str,
        creator_id: str,
        title: str,
        description: str = None,
        assignee_id: str = None,
        tag_names: Optional[Iterable[str]] = None,
    ) -> Task:
        """Create a task. Raises NotFoundError if the project, creator, or
        (when given) assignee don't exist; ValidationError for a bad
        title/description. Tag names are resolved/created via TagService
        (see ``tags.get_or_create_tag``) so a caller never needs a
        pre-existing tag id.
        """
        self._projects.get_project(project_id)
        self._users.get_user(creator_id)
        title = validate_non_empty_str(title, "title", max_length=MAX_TITLE_LENGTH)
        description = validate_optional_str(
            description, "description", max_length=MAX_DESCRIPTION_LENGTH
        )
        if assignee_id is not None:
            self._users.get_user(assignee_id)

        tag_ids = {self._tags.get_or_create_tag(name).id for name in (tag_names or ())}

        task = Task(
            id=ids.new_id(TASK_ID_PREFIX),
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.OPEN,
            creator_id=creator_id,
            created_at=utc_now(),
            assignee_id=assignee_id,
            tag_ids=tag_ids,
        )
        self._store.tasks.save(task.id, task)
        if assignee_id:
            self._notify_assignment(task)
        return task

    def get_task(self, task_id: str) -> Task:
        task_id = validate_id(task_id, "task_id")
        return self._store.tasks.require(task_id)

    def list_tasks(
        self,
        project_id: str = None,
        status: TaskStatus = None,
        assignee_id: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Page[Task]:
        """List tasks, oldest first, with optional project/status/assignee
        filters (each independently optional and combinable).
        """
        items = self._store.tasks.all()
        if project_id is not None:
            items = [t for t in items if t.project_id == project_id]
        if status is not None:
            items = [t for t in items if t.status == status]
        if assignee_id is not None:
            items = [t for t in items if t.assignee_id == assignee_id]
        items.sort(key=lambda t: t.created_at)
        return paginate(items, limit=limit, offset=offset)

    def complete_task(self, task_id: str) -> Task:
        """Mark a task completed. Idempotent: completing an already
        completed task returns it unchanged rather than erroring or
        bumping ``completed_at``.
        """
        task = self.get_task(task_id)
        if task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED
            task.completed_at = utc_now()
        return task

    def assign_task(self, task_id: str, assignee_id: str) -> Task:
        """(Re)assign a task, firing a notification to the new assignee."""
        task = self.get_task(task_id)
        self._users.get_user(assignee_id)
        task.assignee_id = assignee_id
        self._notify_assignment(task)
        return task

    def add_tags(self, task_id: str, tag_names: Iterable[str]) -> Task:
        task = self.get_task(task_id)
        for name in tag_names:
            task.tag_ids.add(self._tags.get_or_create_tag(name).id)
        return task

    def search_tasks(
        self, query: str, project_id: str = None, limit: int = 20, offset: int = 0
    ) -> Page[Task]:
        """Case-insensitive substring search over title + description,
        newest match first, optionally scoped to one project.
        """
        query = validate_non_empty_str(query, "query", max_length=MAX_SEARCH_QUERY_LENGTH).lower()
        items = self._store.tasks.all()
        if project_id is not None:
            items = [t for t in items if t.project_id == project_id]
        items = [t for t in items if query in self._searchable_text(t)]
        items.sort(key=lambda t: t.created_at, reverse=True)
        return paginate(items, limit=limit, offset=offset)

    @staticmethod
    def _searchable_text(task: Task) -> str:
        text = task.title.lower()
        if task.description:
            text += " " + task.description.lower()
        return text

    def _notify_assignment(self, task: Task) -> None:
        if self._notifications is None or not task.assignee_id:
            return
        self._notifications.create_notification(
            user_id=task.assignee_id,
            kind="task_assigned",
            message=f"You were assigned task {task.title!r}",
        )
