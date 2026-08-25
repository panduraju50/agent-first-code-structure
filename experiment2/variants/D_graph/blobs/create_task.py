_tasks = {}
def create_task(pid, title, due_ts=None):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due_ts": due_ts}
    return _tasks[tid]
