"""End-to-end smoke test exercising every Taskly capability. Run: python smoke_test.py"""

from taskly import Taskly
from taskly.errors import ValidationError, AuthError, NotFoundError, ConflictError
from taskly.ids import base62_encode, base62_decode, new_id, short_code
from taskly.dates import now_iso, format_date


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    raise AssertionError(f"expected {exc.__name__}")


def main():
    app = Taskly()

    print("ids / dates")
    check(base62_decode(base62_encode(123456789)) == 123456789, "base62 round-trips")
    check(base62_encode(0) == "0", "base62 encodes zero")
    check(new_id("tsk").startswith("tsk_"), "new_id carries prefix")
    check(len(short_code(8)) == 8, "short_code has fixed length")
    check(len(format_date(now_iso())) > 0, "format_date renders")

    print("users")
    alice = app.users.create("Alice@Example.com ", "Alice", "hunter2pw")
    check(alice["email"] == "alice@example.com", "email normalized")
    check("password_hash" not in alice, "password hash never serialized")
    bob = app.users.create("bob@example.com", "Bob", "password9")
    raises(ConflictError, lambda: app.users.create("alice@example.com", "A2", "password9"))
    raises(ValidationError, lambda: app.users.create("bad-email", "X", "password9"))
    raises(ValidationError, lambda: app.users.create("x@y.com", "X", "short"))

    print("sessions")
    session = app.users.login("alice@example.com", "hunter2pw")
    who = app.users.authenticate(session["token"])
    check(who["id"] == alice["id"], "session resolves to user")
    raises(AuthError, lambda: app.users.login("alice@example.com", "wrong"))
    raises(AuthError, lambda: app.users.authenticate("nope"))

    print("projects")
    proj = app.projects.create(alice["id"], "Launch", "the big launch")
    raises(NotFoundError, lambda: app.projects.create("usr_missing", "X"))
    plist = app.projects.list(owner_id=alice["id"])
    check(plist["total"] == 1 and plist["has_next"] is False, "project list envelope")

    print("tags")
    urgent = app.tags.create(proj["id"], "urgent")
    raises(ConflictError, lambda: app.tags.create(proj["id"], "urgent"))

    print("tasks")
    t = app.tasks.create(proj["id"], alice["id"], "Write spec", "details",
                         assignee_id=bob["id"], tag_ids=[urgent["id"]])
    check(t["status"] == "open" and t["tag_ids"] == [urgent["id"]], "task created with tag")
    # Assigning to bob (not the creator) should have notified bob.
    notes = app.notifications.list(bob["id"])
    check(notes["total"] == 1 and len(notes["items"][0]["ref_code"]) == 8, "assignment notification w/ ref code")

    app.tags.attach(t["id"], urgent["id"])  # idempotent
    reread = app.tasks.list(project_id=proj["id"])["items"][0]
    check(reread["tag_ids"] == [urgent["id"]], "attach is idempotent")

    app.tasks.assign(t["id"], alice["id"])
    done = app.tasks.complete(t["id"])
    check(done["status"] == "done" and done["completed_at"], "task completed")
    check(app.tasks.complete(t["id"])["completed_at"] == done["completed_at"], "complete is idempotent")

    print("search + filter + pagination")
    for i in range(5):
        app.tasks.create(proj["id"], alice["id"], f"Bug {i}")
    found = app.tasks.search("bug", project_id=proj["id"])
    check(found["total"] == 5, "search matches 5 bugs")
    page1 = app.tasks.list(project_id=proj["id"], per_page=2, page=1)
    check(len(page1["items"]) == 2 and page1["has_next"], "pagination window")
    open_only = app.tasks.list(project_id=proj["id"], status="open")
    check(open_only["total"] == 5, "status filter")
    raises(ValidationError, lambda: app.tasks.list(status="bogus"))
    raises(ValidationError, lambda: app.tasks.search(""))

    print("comments")
    app.comments.add(t["id"], bob["id"], "looks good")
    clist = app.comments.list(t["id"])
    check(clist["total"] == 1, "comment listed")
    # alice (creator) should now have a comment notification from bob.
    check(any(n["kind"] == "task_comment" for n in app.notifications.list(alice["id"])["items"]),
          "comment notified creator")

    print("notifications mark-read")
    first = app.notifications.list(bob["id"])["items"][0]
    app.notifications.mark_read(first["id"])
    check(app.notifications.mark_read(first["id"])["read"] is True, "mark_read idempotent")

    print("\nALL SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()
