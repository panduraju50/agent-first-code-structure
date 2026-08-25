"""The single entry point: ``TasklyAPI``.

Construct one ``TasklyAPI()`` per application (or per test) and call
into its ``.users`` / ``.projects`` / ``.tags`` / ``.tasks`` / ``.comments``
/ ``.notifications`` service attributes. This is the only module that
wires services together, and it does so in dependency order:

    store -> users -> projects -> tags -> notifications -> tasks -> comments

(``tasks`` needs ``notifications`` to fire assignment alerts;
``comments`` needs both ``tasks`` and ``notifications``.)

An agent extending Taskly with a new capability should add a new
``<thing>.py`` service module (following the pattern of the existing
ones: one module = one entity/concern, plain-data model in
``models.py``, CRUD via ``store.py``, shared checks via
``validation.py``/``pagination.py``) and wire it in here — this file is
meant to stay a short, readable manifest of "what exists and how it's
connected," not to grow business logic of its own.
"""

from .comments import CommentService
from .notifications import NotificationService
from .projects import ProjectService
from .store import TasklyStore
from .tags import TagService
from .tasks import TaskService
from .users import UserService


class TasklyAPI:
    """Facade over one fully isolated in-memory Taskly instance."""

    def __init__(self):
        self.store = TasklyStore()
        self.users = UserService(self.store)
        self.projects = ProjectService(self.store, self.users)
        self.tags = TagService(self.store)
        self.notifications = NotificationService(self.store, self.users)
        self.tasks = TaskService(
            self.store, self.users, self.projects, self.tags, self.notifications
        )
        self.comments = CommentService(
            self.store, self.users, self.tasks, self.notifications
        )
