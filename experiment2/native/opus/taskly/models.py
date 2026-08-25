"""Entity definitions and serialization. The ONLY place the data shape is declared.

Models are plain dataclasses (dumb records, no behavior). `to_dict` is the single
serializer used by every service, and it strips sensitive fields so a password
hash can never leak through an API response.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List

# Fields never included in serialized output.
_SENSITIVE = {"password_hash"}

# Task lifecycle states (used by validation.one_of at the service boundary).
TASK_STATUSES = {"open", "done"}


@dataclass
class User:
    id: str
    email: str
    name: str
    password_hash: str
    created_at: str


@dataclass
class Session:
    token: str
    user_id: str
    created_at: str


@dataclass
class Project:
    id: str
    name: str
    owner_id: str
    description: str
    created_at: str


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    description: str
    status: str
    creator_id: str
    assignee_id: Optional[str]
    tag_ids: List[str]
    created_at: str
    completed_at: Optional[str]


@dataclass
class Tag:
    id: str
    name: str
    project_id: str
    created_at: str


@dataclass
class Comment:
    id: str
    task_id: str
    author_id: str
    body: str
    created_at: str


@dataclass
class Notification:
    id: str
    user_id: str
    kind: str
    message: str
    ref_code: str
    read: bool
    created_at: str


def to_dict(obj) -> dict:
    """Serialize any model, dropping sensitive fields. The single serializer."""
    data = asdict(obj)
    for key in _SENSITIVE:
        data.pop(key, None)
    return data
