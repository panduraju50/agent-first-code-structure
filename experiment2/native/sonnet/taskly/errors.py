"""All exceptions Taskly raises, in one place.

Every service module raises only these types (never a bare Exception or a
stdlib exception) so a caller — human or agent — can catch failures by
kind without knowing which module they came from.
"""


class TasklyError(Exception):
    """Base class for every error Taskly raises. Catch this to catch anything."""


class ValidationError(TasklyError):
    """Input failed validation (bad shape, bad format, out of range)."""


class NotFoundError(TasklyError):
    """A referenced entity (user, project, task, tag, ...) does not exist."""


class AuthError(TasklyError):
    """Authentication or session validation failed."""


class ConflictError(TasklyError):
    """The operation conflicts with existing state (e.g. duplicate email)."""
