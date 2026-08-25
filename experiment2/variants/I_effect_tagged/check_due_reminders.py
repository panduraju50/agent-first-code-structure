# effects: ['store', 'net']
_reminded = set()
def check_due_reminders(now, window_seconds=172800):
    # Scans tasks for ones nearing their due date and notifies the assignee.
    # "near" = due within `window_seconds` from `now` (default 48h), not overdue,
    # not already done, has an assignee, and not already reminded once.
    sent = []
    for t in _tasks.values():
        if t.get("done"):
            continue
        due = t.get("due")
        if due is None:
            continue
        uid = t.get("assignee")
        if uid is None:
            continue
        key = (t["id"], uid)
        if key in _reminded:
            continue
        delta = due - now
        if 0 <= delta <= window_seconds:
            user = get_user(uid)
            if user is None:
                continue
            msg = "Task '" + t["title"] + "' is due " + format_date(due)
            n = notify(user["id"], msg, t["id"])
            _reminded.add(key)
            sent.append(n)
    return sent
