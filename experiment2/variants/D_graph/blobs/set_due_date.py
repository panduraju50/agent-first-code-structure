def set_due_date(tid, due_ts):
    # NOTE: like complete_task() and assign_task(), this does not check that
    # tid exists first -- a bad tid raises KeyError instead of a clean error.
    # Kept consistent with the existing style rather than silently fixed here.
    _tasks[tid]["due_ts"] = due_ts
    return _tasks[tid]
