"""Projects: create and list.

A ``Project`` belongs to exactly one owner (a ``User``). This module owns
``store.projects`` exclusively.
"""

from . import ids
from .dates import utc_now
from .models import Project
from .pagination import Page, paginate
from .store import TasklyStore
from .users import UserService
from .validation import validate_id, validate_non_empty_str, validate_optional_str

PROJECT_ID_PREFIX = "prj"
MAX_NAME_LENGTH = 140
MAX_DESCRIPTION_LENGTH = 2000


class ProjectService:
    def __init__(self, store: TasklyStore, users: UserService):
        self._store = store
        self._users = users

    def create_project(self, owner_id: str, name: str, description: str = None) -> Project:
        """Create a project. Raises NotFoundError if ``owner_id`` doesn't
        resolve to a real user, ValidationError for a bad name/description.
        """
        self._users.get_user(owner_id)  # existence check; raises NotFoundError
        name = validate_non_empty_str(name, "name", max_length=MAX_NAME_LENGTH)
        description = validate_optional_str(
            description, "description", max_length=MAX_DESCRIPTION_LENGTH
        )
        project = Project(
            id=ids.new_id(PROJECT_ID_PREFIX),
            owner_id=owner_id,
            name=name,
            description=description,
            created_at=utc_now(),
        )
        self._store.projects.save(project.id, project)
        return project

    def get_project(self, project_id: str) -> Project:
        project_id = validate_id(project_id, "project_id")
        return self._store.projects.require(project_id)

    def list_projects(self, owner_id: str = None, limit: int = 20, offset: int = 0) -> Page[Project]:
        """List projects, oldest first, optionally scoped to one owner."""
        items = self._store.projects.all()
        if owner_id is not None:
            items = [p for p in items if p.owner_id == owner_id]
        items.sort(key=lambda p: p.created_at)
        return paginate(items, limit=limit, offset=offset)
