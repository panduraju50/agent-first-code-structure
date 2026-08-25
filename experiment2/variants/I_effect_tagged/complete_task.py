# effects: ['store']
def complete_task(tid):
    _tasks[tid]["done"] = True
    return _tasks[tid]
