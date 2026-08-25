from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    assignee_id: Optional[str] = None
