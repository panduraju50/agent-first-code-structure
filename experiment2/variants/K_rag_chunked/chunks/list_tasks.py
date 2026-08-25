"""@card
purpose: list tasks in a project
api: list_tasks(pid)->list
tags: tasks, list tasks
effects: ['store']
deps: []
"""

def list_tasks(pid):
    return [t for t in _tasks.values() if t["pid"] == pid]
