"""@card
purpose: set or change a task's due date
api: set_due_date(tid,due_ts)->dict
tags: tasks, due date, set due date, reminder
effects: ['store']
deps: []
"""

def set_due_date(tid, due_ts):
    # NOTE: no existence check on tid (same convention as assign_task/complete_task) -> KeyError if tid unknown
    if due_ts is not None and due_ts < 0:
        raise ValueError("bad due date")
    _tasks[tid]["due_ts"] = due_ts
    _tasks[tid]["reminded"] = False  # changing the due date re-arms the reminder
    return _tasks[tid]
