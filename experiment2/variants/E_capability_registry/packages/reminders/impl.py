DEFAULT_THRESHOLD = 86400  # 1 day, in seconds


def check_due_reminders(now_ts, threshold_seconds=DEFAULT_THRESHOLD):
    # Scans tasks the same way packages/search does (bare `_tasks`, defined in
    # packages/tasks/impl.py, reached via the shared capability namespace rather
    # than an import -- follows the existing cross-package convention in this repo).
    #
    # A task gets a reminder when all of:
    #   - it has a due_date set (packages/tasks.set_due_date)
    #   - it is not done
    #   - it has an assignee (nothing to notify otherwise)
    #   - due_date is in [now_ts, now_ts + threshold_seconds]  (near, not overdue-only,
    #     and not "any time in the future")
    #   - it has not already been reminded for this due_date (t["reminded"], reset by
    #     set_due_date whenever the due date changes, so edits re-arm the reminder)
    #
    # `seq` is a per-call counter passed into notify()'s sequence arg, matching how
    # notifications/impl.py expects an incrementing seq per notification.
    sent = []
    seq = 0
    for t in _tasks.values():
        due = t.get("due_date")
        if due is None:
            continue
        if t.get("done"):
            continue
        assignee = t.get("assignee")
        if assignee is None:
            continue
        if t.get("reminded"):
            continue
        if due < now_ts or due - now_ts > threshold_seconds:
            continue
        seq += 1
        msg = "Task '%s' is due %s" % (t["title"], format_date(due))
        n = notify(assignee, msg, seq)
        t["reminded"] = True
        sent.append(n)
    return sent
