"""Taskly facade: the single entry point that wires the store and all services.

    from taskly import Taskly
    app = Taskly()
    alice = app.users.create("alice@example.com", "Alice", "hunter2pw")
    proj  = app.projects.create(alice["id"], "Launch")
    task  = app.tasks.create(proj["id"], alice["id"], "Write spec")

Each capability is reached through its service attribute (app.users, app.tasks,
...). Construction order encodes the dependency graph declared in services/__init__.
"""

from .store import Store
from .services import (
    UserService,
    ProjectService,
    TaskService,
    TagService,
    CommentService,
    NotificationService,
)


class Taskly:
    def __init__(self, store: Store = None):
        self.store = store or Store()

        # Leaf services first (no service dependencies).
        self.users = UserService(self.store)
        self.projects = ProjectService(self.store)
        self.tags = TagService(self.store)
        self.notifications = NotificationService(self.store)

        # Composite services depend on the leaves above.
        self.tasks = TaskService(self.store, self.tags, self.notifications)
        self.comments = CommentService(self.store, self.notifications)
