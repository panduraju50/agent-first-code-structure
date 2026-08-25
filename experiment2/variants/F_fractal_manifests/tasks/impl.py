_tasks = {}
def create_task(pid, title, due=None):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due": due}
    return _tasks[tid]


def set_due_date(tid, due):
    # P6: no existence check anywhere else in this module either (complete_task/assign_task
    # below have the same gap) - KeyError leaks straight out to the caller on a bad tid
    if tid not in _tasks: raise KeyError("no such task")
    _tasks[tid]["due"] = due
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
