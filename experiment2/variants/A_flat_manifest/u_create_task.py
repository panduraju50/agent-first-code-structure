_tasks = {}
def create_task(pid, title, due=None):
    if not validate_title(title): raise ValueError("bad title")
    # NOTE: due is optional at creation time; use set_due_date to add/change it later.
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due": due, "reminded": False}
    return _tasks[tid]
