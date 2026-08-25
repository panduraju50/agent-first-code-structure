# Taskly — Capability Map

Navigation index for an AI agent. Every capability maps to exactly one file, and
every cross-cutting concern (ids, validation, dates, pagination, serialization,
persistence, errors) lives in exactly one place. To change a rule, edit its home
file; nothing is duplicated.

## Entry point
- `taskly/api.py` — `Taskly` facade. Construct it, reach every capability via
  `app.users`, `app.projects`, `app.tasks`, `app.tags`, `app.comments`,
  `app.notifications`.

## Foundation (shared, no domain logic) — edit here to change a rule everywhere
| Concern                         | File                    | Key symbols |
|---------------------------------|-------------------------|-------------|
| Base62 ids + short ref codes    | `taskly/ids.py`         | `base62_encode`, `new_id`, `short_code` |
| Input validation rules          | `taskly/validation.py`  | `validate_email`, `validate_str`, `validate_int`, `validate_password`, `one_of` |
| Password hashing + tokens       | `taskly/security.py`    | `hash_password`, `verify_password`, `new_session_token` |
| Timestamps + date formatting    | `taskly/dates.py`       | `now_iso`, `format_date`, `parse_iso` |
| Pagination envelope             | `taskly/pagination.py`  | `paginate` |
| Entity shapes + serialization   | `taskly/models.py`      | dataclasses, `to_dict` (strips `password_hash`) |
| Persistence + `get_or_404`      | `taskly/store.py`       | `Store` |
| Error taxonomy                  | `taskly/errors.py`      | `TasklyError`, `ValidationError`, `AuthError`, `NotFoundError`, `ConflictError` |

## Domain services (one per entity) — `taskly/services/`
| Capability                                    | File               | Depends on |
|-----------------------------------------------|--------------------|------------|
| user create/get, login, session auth          | `users.py`         | — |
| project create/list                           | `projects.py`      | — |
| tag create/list/attach, tag-id resolution     | `tags.py`          | — |
| notification create (ref code)/list/mark-read | `notifications.py` | — |
| task create/list/complete/assign/search       | `tasks.py`         | tags, notifications |
| comment add/list                              | `comments.py`      | notifications |

## Conventions (uniform across all services)
- Services accept/return **plain dicts** (via `models.to_dict`), never raw models.
- List and search methods return the `paginate(...)` envelope.
- Missing entities -> `store.get_or_404(...)` -> `NotFoundError`.
- Timestamps stored as canonical UTC ISO (`...Z`); render with `dates.format_date`.

## Verify
- `python smoke_test.py` — end-to-end exercise of every capability.
