"""Taskly: a small in-memory task/project API.

Public surface:
    from taskly import Taskly          # the facade you construct
    from taskly.errors import TasklyError, ValidationError, NotFoundError, ...

See MANIFEST.md at the repo root for the capability -> file map.
"""

from .api import Taskly
from . import errors

__all__ = ["Taskly", "errors"]
