from impl.notifications import notify
from impl.dates import format_date

_tasks = {}
_reminder_seq = 0


def create_task(pid, title, due_ts=None):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {
        "id": tid, "pid": pid, "title": title, "done": False, "assignee": None,
        "due_ts": due_ts, "reminded": False,
    }
    return _tasks[tid]


def list_tasks(pid):
    return [t for t in _tasks.values() if t["pid"] == pid]


def complete_task(tid):
    _tasks[tid]["done"] = True
    return _tasks[tid]


def assign_task(tid, uid, actor):
    # P4: no permission check that `actor` may assign within this task's project
    _tasks[tid]["assignee"] = uid
    return _tasks[tid]


def set_due_date(tid, ts):
    _tasks[tid]["due_ts"] = ts
    _tasks[tid]["reminded"] = False  # due date moved: allow a fresh reminder
    return _tasks[tid]


def check_due_reminders(now_ts, window_seconds=86400):
    """Notify each task's assignee once when the task is nearing its due
    date. A task is "near due" when 0 <= due_ts - now_ts <= window_seconds.
    Done tasks, tasks with no assignee, tasks with no due date, and tasks
    already reminded (until the due date is changed via set_due_date) are
    skipped. Returns the list of notifications sent, in task-id order.
    """
    global _reminder_seq
    sent = []
    for tid in sorted(_tasks):
        t = _tasks[tid]
        if t["done"]:
            continue
        if t["assignee"] is None:
            continue
        if t["due_ts"] is None:
            continue
        if t.get("reminded"):
            continue
        remaining = t["due_ts"] - now_ts
        if 0 <= remaining <= window_seconds:
            _reminder_seq += 1
            msg = "Task '%s' is due %s" % (t["title"], format_date(t["due_ts"]))
            n = notify(t["assignee"], msg, _reminder_seq)
            t["reminded"] = True
            sent.append(n)
    return sent
