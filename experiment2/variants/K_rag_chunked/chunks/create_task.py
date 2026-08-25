"""@card
purpose: create a task in a project
api: create_task(pid,title)->dict
tags: tasks, create task
effects: ['store']
deps: ['validate_title']
"""

_tasks = {}
def create_task(pid, title):
    if not validate_title(title): raise ValueError("bad title")
    tid = len(_tasks) + 1
    # due_ts starts unset; set via set_due_date. reminded flag lets check_due_reminders dedupe.
    _tasks[tid] = {"id": tid, "pid": pid, "title": title, "done": False, "assignee": None, "due_ts": None, "reminded": False}
    return _tasks[tid]
