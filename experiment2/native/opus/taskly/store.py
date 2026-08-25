"""In-memory data store. The ONLY place entities are persisted and looked up.

Swappable for a real database later: every service reads/writes through this
object and through `get_or_404`, so lookup semantics live in one method.
"""

from .errors import NotFoundError


class Store:
    def __init__(self):
        # id -> model instance
        self.users = {}
        self.projects = {}
        self.tasks = {}
        self.tags = {}
        self.comments = {}
        self.notifications = {}
        # token -> Session
        self.sessions = {}

    @staticmethod
    def get_or_404(collection: dict, key: str, entity: str):
        """Fetch by id or raise NotFoundError. The single lookup path."""
        obj = collection.get(key)
        if obj is None:
            raise NotFoundError(f"{entity} not found: {key}")
        return obj
