# effects: ['store']
_tasks = {}
def create_task(pid, title, due=None):
    if not validate_title(title): raise ValueError("bad title")
    if due is not None and (not isinstance(due, (int, float)) or due < 0):
        raise ValueError("bad due")
    tid = len(_tasks) + 1
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due": due}
    return _tasks[tid]
