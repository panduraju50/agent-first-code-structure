_remind_seq = 0
def remind_due(now, within=86400):
    # Send a due-date reminder to each task's assignee when the task is
    # not done, has a due date, and is due within `within` seconds
    # (inclusive) of `now`. Overdue-but-open tasks (due <= now) are
    # included so a missed deadline still notifies. Reuses notifications.notify
    # and dates.format_date instead of re-implementing either.
    global _remind_seq
    sent = []
    for t in _tasks.values():
        if t.get("done"):
            continue
        due = t.get("due")
        if due is None:
            continue
        uid = t.get("assignee")
        if uid is None:            # unassigned: nobody to notify
            continue
        if due - now <= within:    # near or already past the due date
            msg = "Task '{}' is due {}".format(t["title"], format_date(due))
            _remind_seq += 1
            sent.append(notify(uid, msg, _remind_seq))
    return sent
