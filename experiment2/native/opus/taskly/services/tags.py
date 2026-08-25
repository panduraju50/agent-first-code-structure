"""Tags: create (unique per project), list, attach to a task.

`resolve_ids` is the shared validation used by TaskService when tags are passed
at task-create time, keeping tag-membership logic in one place.
"""

from .. import validation
from ..errors import ConflictError, ValidationError
from ..models import Tag, to_dict
from ..ids import new_id
from ..dates import now_iso
from ..pagination import paginate, DEFAULT_PER_PAGE


class TagService:
    def __init__(self, store):
        self.store = store

    def create(self, project_id: str, name: str) -> dict:
        self.store.get_or_404(self.store.projects, project_id, "project")
        name = validation.validate_str(name, "name", min_len=1, max_len=60)

        if self._find(project_id, name) is not None:
            raise ConflictError(f"tag already exists in project: {name}")

        tag = Tag(id=new_id("tag"), name=name, project_id=project_id, created_at=now_iso())
        self.store.tags[tag.id] = tag
        return to_dict(tag)

    def list(self, project_id: str, page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
        items = [t for t in self.store.tags.values() if t.project_id == project_id]
        items.sort(key=lambda t: t.created_at)
        return paginate([to_dict(t) for t in items], page, per_page)

    def attach(self, task_id: str, tag_id: str) -> dict:
        task = self.store.get_or_404(self.store.tasks, task_id, "task")
        tag = self.store.get_or_404(self.store.tags, tag_id, "tag")
        if tag.project_id != task.project_id:
            raise ValidationError("tag and task belong to different projects")
        if tag_id not in task.tag_ids:
            task.tag_ids.append(tag_id)
        return to_dict(task)

    def resolve_ids(self, project_id: str, tag_ids) -> list:
        """Validate a list of tag ids all exist and belong to the project."""
        resolved = []
        for tag_id in tag_ids or []:
            tag = self.store.get_or_404(self.store.tags, tag_id, "tag")
            if tag.project_id != project_id:
                raise ValidationError(f"tag {tag_id} does not belong to project {project_id}")
            if tag_id not in resolved:
                resolved.append(tag_id)
        return resolved

    def _find(self, project_id: str, name: str):
        return next(
            (t for t in self.store.tags.values()
             if t.project_id == project_id and t.name == name),
            None,
        )
