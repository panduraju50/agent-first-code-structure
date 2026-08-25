_reminder_seq = 0

def check_due_reminders(now_ts, window_seconds):
    # Scans all tasks and notifies each task's assignee when the task is
    # unfinished and its due_ts falls within [now_ts, now_ts + window_seconds]
    # (due soon, not yet overdue -- already-overdue tasks are intentionally
    # NOT re-notified here since there is no "already notified" tracking;
    # see the missing-edge-case note about that).
    #
    # Skips: tasks with no due date, tasks with no assignee, and tasks whose
    # assignee id no longer resolves to a real user -- assign_task() does not
    # validate uid (see P4 in assign_task.py), so a task can carry a "ghost"
    # assignee; get_user() is used here (not re-implemented) to guard against
    # notifying a uid that doesn't exist.
    global _reminder_seq
    sent = []
    for t in _tasks.values():
        if t.get("done"):
            continue
        due = t.get("due_ts")
        if due is None:
            continue
        uid = t.get("assignee")
        if uid is None:
            continue
        if get_user(uid) is None:
            continue
        if now_ts <= due <= now_ts + window_seconds:
            _reminder_seq += 1
            sent.append(notify(uid, "Task '%s' is due soon" % t["title"], _reminder_seq))
    return sent
