"""Plain-data entity definitions.

These dataclasses hold state only — no validation, no persistence, no
business rules. All of that lives in the matching service module
(``users.py`` owns ``User``, ``tasks.py`` owns ``Task``, etc.). Keeping
models "dumb" means there is exactly one place (the service) that can
mutate an entity's invariants, which is what makes it possible to audit
for duplicate logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Set


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    created_at: datetime


@dataclass
class Project:
    id: str
    owner_id: str
    name: str
    description: Optional[str]
    created_at: datetime


@dataclass
class Tag:
    id: str
    name: str


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    creator_id: str
    created_at: datetime
    assignee_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    tag_ids: Set[str] = field(default_factory=set)


@dataclass
class Comment:
    id: str
    task_id: str
    author_id: str
    body: str
    created_at: datetime


@dataclass
class Notification:
    id: str
    user_id: str
    reference_code: str
    kind: str
    message: str
    created_at: datetime
    read: bool = False
