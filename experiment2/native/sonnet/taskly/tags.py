"""Tags: get-or-create by name, list.

Tags are global (not scoped to a project or task) and deduplicated by
normalized (trimmed, lowercased) name via ``store.tag_name_index`` — two
calls to ``get_or_create_tag("Bug")`` and ``get_or_create_tag(" bug ")``
return the same ``Tag``. This module owns ``store.tags`` and
``store.tag_name_index`` exclusively.
"""

from . import ids
from .models import Tag
from .store import TasklyStore
from .validation import validate_id, validate_non_empty_str

TAG_ID_PREFIX = "tag"
MAX_NAME_LENGTH = 40


class TagService:
    def __init__(self, store: TasklyStore):
        self._store = store

    def get_or_create_tag(self, name: str) -> Tag:
        name = validate_non_empty_str(name, "name", max_length=MAX_NAME_LENGTH).lower()
        existing_id = self._store.tag_name_index.get(name)
        if existing_id:
            return self._store.tags.require(existing_id)
        tag = Tag(id=ids.new_id(TAG_ID_PREFIX), name=name)
        self._store.tags.save(tag.id, tag)
        self._store.tag_name_index[name] = tag.id
        return tag

    def get_tag(self, tag_id: str) -> Tag:
        tag_id = validate_id(tag_id, "tag_id")
        return self._store.tags.require(tag_id)

    def list_tags(self) -> list:
        """All tags, alphabetical. Unbounded (tags are a small, bounded
        vocabulary in practice) — unlike the entity list_* methods this
        deliberately does not paginate.
        """
        return sorted(self._store.tags.all(), key=lambda t: t.name)
