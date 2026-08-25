"""tasks domain service.

Depends on core (id encoding + title validation) only. Must never import
domains.users — the boundary enforcer fails the build if it does.

Note: `assign` intentionally does NOT verify that assignee_id refers to a
real user. Doing so would require importing domains.users, which Design D
forbids. Cross-domain checks like that belong in the composition root
(see app/main.py), the only layer allowed to know about both domains.
"""

from core.ids import new_id
from core.validation import validate_title
from domains.tasks.models import Task


class TaskStore:
    """In-memory task store: create/list/assign."""

    def __init__(self):
        self._tasks = {}
        self._counter = 0

    def create(self, title: str) -> Task:
        title = validate_title(title)
        self._counter += 1
        task_id = new_id(self._counter)
        task = Task(id=task_id, title=title)
        self._tasks[task_id] = task
        return task

    def list(self):
        return list(self._tasks.values())

    def get(self, task_id: str) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise KeyError(f"no such task: {task_id}") from None

    def assign(self, task_id: str, assignee_id: str) -> Task:
        task = self.get(task_id)
        updated = Task(id=task.id, title=task.title, assignee_id=assignee_id)
        self._tasks[task_id] = updated
        return updated
