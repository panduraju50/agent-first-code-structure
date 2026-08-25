"""@card
purpose: mark a task done
api: complete_task(tid)->dict
tags: tasks, complete task
effects: ['store']
deps: []
"""

def complete_task(tid):
    _tasks[tid]["done"] = True
    return _tasks[tid]
