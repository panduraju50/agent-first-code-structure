def set_due_date(tid, ts):
    # NOTE: no authorization check (actor not passed) -- consistent with the
    # rest of this module (complete_task, assign_task) which are equally
    # unauthenticated. Flagged as a missing edge case, not fixed here.
    if tid not in _tasks: raise ValueError("no such task")
    if ts is not None and ts < 0: raise ValueError("bad due date")
    _tasks[tid]["due"] = ts
    _tasks[tid]["reminded"] = False  # due date changed -> allow a fresh reminder
    return _tasks[tid]
