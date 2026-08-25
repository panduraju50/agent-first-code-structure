"""Pagination. The ONLY place list results get windowed.

Every service `list`/`search` returns the dict produced by `paginate`, so the
response envelope is identical everywhere.
"""

from .validation import validate_int

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


def paginate(items: list, page: int = 1, per_page: int = DEFAULT_PER_PAGE) -> dict:
    page = validate_int(page, "page", min_value=1)
    per_page = validate_int(per_page, "per_page", min_value=1, max_value=MAX_PER_PAGE)

    total = len(items)
    total_pages = (total + per_page - 1) // per_page if total else 0
    start = (page - 1) * per_page
    window = items[start:start + per_page]

    return {
        "items": window,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1 and total > 0,
    }
