_tasks = {}
def create_task(pid, title, due=None):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due": due}
    return _tasks[tid]
