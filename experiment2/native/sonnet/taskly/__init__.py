"""Taskly: a small in-memory task/project API.

Package map (read this first when navigating or extending):

    api.py            TasklyAPI facade — construct this, use its .users/
                       .projects/.tags/.tasks/.comments/.notifications
    models.py          Plain-data entities (User, Project, Task, Tag,
                       Comment, Notification, TaskStatus)
    store.py           In-memory Repository[T] + TasklyStore (all state)
    errors.py           Exception hierarchy (TasklyError and subclasses)

    users.py            UserService: create/get user, auth, sessions
    projects.py         ProjectService: create/list projects
    tags.py             TagService: get-or-create/list tags
    tasks.py            TaskService: create/list/complete/assign/search
    comments.py         CommentService: add/list comments
    notifications.py    NotificationService: create/list, reference codes

    ids.py              base62 id + short reference-code generation
    validation.py       shared input validation (email, strings, ids)
    dates.py             UTC datetime formatting/parsing
    pagination.py        generic Page/paginate() used by every list/search

Each entity is owned by exactly one service module, which is the only
module allowed to mutate that entity's repository in ``store.py``. Cross-
entity operations (e.g. "assigning a task notifies the assignee") are
expressed by one service holding a reference to another (see
``TaskService.__init__`` / ``CommentService.__init__``), wired once in
``api.TasklyAPI.__init__``.

Typical usage:

    from taskly import TasklyAPI

    api = TasklyAPI()
    user = api.users.create_user("ada@example.com", "hunter2pass")
    session = api.users.authenticate("ada@example.com", "hunter2pass")
    project = api.projects.create_project(user.id, "Analytical Engine")
    task = api.tasks.create_task(project.id, user.id, "Design the mill")
    api.tasks.complete_task(task.id)
"""

from .api import TasklyAPI
from .errors import AuthError, ConflictError, NotFoundError, TasklyError, ValidationError
from .models import Comment, Notification, Project, Tag, Task, TaskStatus, User
from .pagination import Page

__all__ = [
    "TasklyAPI",
    "TasklyError",
    "ValidationError",
    "NotFoundError",
    "AuthError",
    "ConflictError",
    "User",
    "Project",
    "Task",
    "TaskStatus",
    "Tag",
    "Comment",
    "Notification",
    "Page",
]
