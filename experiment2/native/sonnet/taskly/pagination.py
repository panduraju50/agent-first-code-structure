"""Generic in-memory pagination.

Every ``list_*``/``search_*`` method across the service layer returns a
``Page`` produced by ``paginate()``, so there is exactly one definition of
what "limit", "offset", "total", and "has_more" mean in this codebase.
"""

from dataclasses import dataclass
from typing import Generic, List, Optional, Sequence, TypeVar

from .errors import ValidationError

T = TypeVar("T")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass
class Page(Generic[T]):
    """One page of results plus enough metadata to fetch the next page."""

    items: List[T]
    total: int
    limit: int
    offset: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total

    @property
    def next_offset(self) -> Optional[int]:
        return self.offset + self.limit if self.has_more else None


def validate_pagination(limit: int = DEFAULT_LIMIT, offset: int = 0):
    """Validate limit/offset, returning them unchanged on success.

    Rejects bool (which is a subclass of int in Python — ``True``/``False``
    silently passing as 1/0 would be a confusing bug) as well as
    out-of-range or non-integer values.
    """
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValidationError("limit must be an integer")
    if not isinstance(offset, int) or isinstance(offset, bool):
        raise ValidationError("offset must be an integer")
    if limit <= 0:
        raise ValidationError("limit must be positive")
    if limit > MAX_LIMIT:
        raise ValidationError(f"limit must be at most {MAX_LIMIT}")
    if offset < 0:
        raise ValidationError("offset must not be negative")
    return limit, offset


def paginate(items: Sequence[T], limit: int = DEFAULT_LIMIT, offset: int = 0) -> Page[T]:
    """Slice ``items`` (already filtered/sorted by the caller) into a Page.

    ``items`` is assumed to already reflect the full, ordered result set;
    this function only handles the limit/offset windowing and total count.
    """
    limit, offset = validate_pagination(limit, offset)
    total = len(items)
    page_items = list(items[offset : offset + limit])
    return Page(items=page_items, total=total, limit=limit, offset=offset)
