"""Domain services, one module per entity. Wired together by taskly.api.Taskly.

Dependency order (bottom to top):
    notifications  ->  (none)
    users          ->  (none)
    projects       ->  (none)
    tags           ->  (none)
    tasks          ->  tags, notifications
    comments       ->  notifications
"""

from .users import UserService
from .projects import ProjectService
from .tasks import TaskService
from .tags import TagService
from .comments import CommentService
from .notifications import NotificationService

__all__ = [
    "UserService",
    "ProjectService",
    "TaskService",
    "TagService",
    "CommentService",
    "NotificationService",
]
