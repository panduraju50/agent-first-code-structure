"""In-memory persistence.

``Repository`` is a generic id -> entity map that centralizes the
CRUD primitives (save/get/require/delete/filter) so no service module
reimplements "look up by id or raise NotFoundError" on its own dict.

``TasklyStore`` bundles one ``Repository`` per entity type plus a couple
of secondary indexes (email -> user id, tag name -> tag id) that exist
purely to keep lookups O(1) instead of scanning ``.all()``. If Taskly ever
grows a real database backend, this is the one module that would be
replaced — every service module talks to the store through this
interface, never to raw dicts.
"""

from typing import Callable, Dict, Generic, List, Optional, TypeVar

from .errors import NotFoundError
from .security import Session

T = TypeVar("T")


class Repository(Generic[T]):
    """Generic in-memory repository keyed by entity id."""

    def __init__(self, entity_name: str):
        self._entity_name = entity_name
        self._items: Dict[str, T] = {}

    def save(self, item_id: str, item: T) -> T:
        self._items[item_id] = item
        return item

    def get(self, item_id: str) -> Optional[T]:
        return self._items.get(item_id)

    def require(self, item_id: str) -> T:
        """Look up by id or raise NotFoundError with a message naming the
        entity type — the single place that error message is worded.
        """
        item = self._items.get(item_id)
        if item is None:
            raise NotFoundError(f"{self._entity_name} {item_id!r} not found")
        return item

    def delete(self, item_id: str) -> None:
        self._items.pop(item_id, None)

    def all(self) -> List[T]:
        return list(self._items.values())

    def filter(self, predicate: Callable[[T], bool]) -> List[T]:
        return [item for item in self._items.values() if predicate(item)]

    def exists(self, item_id: str) -> bool:
        return item_id in self._items

    def __len__(self) -> int:
        return len(self._items)


class TasklyStore:
    """All state for one Taskly "database" instance.

    One ``TasklyStore`` (usually created via ``TasklyAPI()``) is fully
    isolated from any other — there is no global/shared state anywhere in
    this package, which is what makes the service layer safe to
    unit-test in parallel.
    """

    def __init__(self):
        self.users: Repository = Repository("user")
        self.projects: Repository = Repository("project")
        self.tasks: Repository = Repository("task")
        self.tags: Repository = Repository("tag")
        self.comments: Repository = Repository("comment")
        self.notifications: Repository = Repository("notification")

        # Sessions are keyed by opaque token, not by an entity id, so they
        # get a plain dict rather than a Repository.
        self.sessions: Dict[str, Session] = {}

        # Secondary indexes for uniqueness + O(1) lookup.
        self.email_index: Dict[str, str] = {}  # normalized email -> user_id
        self.tag_name_index: Dict[str, str] = {}  # normalized tag name -> tag_id
