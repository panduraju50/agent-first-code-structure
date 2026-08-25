_tasks = {}
def create_task(pid, title, due_date=None):
    if not validate_title(title): raise ValueError("bad title")
    if due_date is not None and not validate_date(due_date): raise ValueError("bad due_date")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due_date": due_date}
    return _tasks[tid]
