"""Projects: create and list (paginated)."""

from .. import validation
from ..models import Project, to_dict
from ..ids import new_id
from ..dates import now_iso
from ..pagination import paginate, DEFAULT_PER_PAGE


class ProjectService:
    def __init__(self, store):
        self.store = store

    def create(self, owner_id: str, name: str, description: str = "") -> dict:
        self.store.get_or_404(self.store.users, owner_id, "user")
        name = validation.validate_str(name, "name", min_len=1, max_len=120)
        description = validation.validate_str(description or "", "description", max_len=2000)

        project = Project(
            id=new_id("prj"),
            name=name,
            owner_id=owner_id,
            description=description,
            created_at=now_iso(),
        )
        self.store.projects[project.id] = project
        return to_dict(project)

    def list(self, owner_id: str = None, page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        items = [
            p for p in self.store.projects.values()
            if owner_id is None or p.owner_id == owner_id
        ]
        items.sort(key=lambda p: p.created_at)
        return paginate([to_dict(p) for p in items], page, per_page)
