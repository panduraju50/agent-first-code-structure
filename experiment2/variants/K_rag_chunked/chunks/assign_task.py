"""@card
purpose: assign a task to a user
api: assign_task(tid,uid,actor)->dict
tags: tasks, assign task
effects: ['store']
deps: []
"""

def assign_task(tid, uid, actor):
    # P4: no permission check that `actor` may assign within this task's project
    _tasks[tid]["assignee"] = uid
    return _tasks[tid]
