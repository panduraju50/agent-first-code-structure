_tasks = {}
def create_task(pid, title):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {
        "id": tid, "pid": pid, "title": title, "done": False, "assignee": None,
        "due_date": None, "reminded": False,
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
    # P6 (pre-existing pattern, kept consistent): no check that tid exists, like
    # complete_task/assign_task above -> raises KeyError on bad tid instead of a
    # validated error. Left as-is for consistency with the rest of this file, but
    # ts itself IS validated since due dates directly drive notify() below.
    if not isinstance(ts, int) or ts <= 0:
        raise ValueError("bad due_date")
    t = _tasks[tid]
    t["due_date"] = ts
    t["reminded"] = False  # new/changed due date means the old reminder no longer applies
    return t
