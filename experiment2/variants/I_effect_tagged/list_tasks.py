# effects: ['store']
def list_tasks(pid):
    return [t for t in _tasks.values() if t["pid"] == pid]
