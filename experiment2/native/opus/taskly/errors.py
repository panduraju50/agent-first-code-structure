"""All exception types raised by Taskly. Single source of truth for error taxonomy.

Every service raises one of these; callers catch `TasklyError` for a blanket
handler or a specific subclass. Each carries an HTTP-ish `status` so a web layer
can map errors without re-classifying them.
"""


class TasklyError(Exception):
    """Base for every Taskly error. Never raised directly."""

    status = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def to_dict(self) -> dict:
        return {"error": type(self).__name__, "message": self.message, "status": self.status}


class ValidationError(TasklyError):
    """Input failed a validation rule (bad email, missing field, out-of-range)."""

    status = 400


class AuthError(TasklyError):
    """Authentication/authorization failed (bad password, invalid session)."""

    status = 401


class NotFoundError(TasklyError):
    """A referenced entity does not exist."""

    status = 404


class ConflictError(TasklyError):
    """The request conflicts with existing state (duplicate email/tag)."""

    status = 409
