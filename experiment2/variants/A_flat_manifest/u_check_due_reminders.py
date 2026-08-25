DEFAULT_REMINDER_WINDOW = 86400  # 1 day, in seconds (matches dates.format_date's day-granularity)

def check_due_reminders(now_ts, window_seconds=DEFAULT_REMINDER_WINDOW):
    # Feature: task due-date reminder.
    # Scans all tasks and sends one notification per task whose due date is
    # coming up soon (within `window_seconds`, not yet overdue) to its
    # assignee, then marks it so the same task doesn't re-notify on every
    # call. Skips: tasks with no due date, tasks already done, tasks with no
    # assignee, tasks whose assignee id no longer resolves to a real user
    # (assign_task does not validate uid -- see P4/assign_task), tasks
    # already overdue (delta < 0 -- overdue is a different feature/alert),
    # and tasks already reminded since the due date was last set.
    sent = []
    for t in _tasks.values():
        due = t.get("due")
        if due is None:
            continue
        if t["done"]:
            continue
        uid = t["assignee"]
        if uid is None:
            continue
        if get_user(uid) is None:
            continue
        if t.get("reminded"):
            continue
        delta = due - now_ts
        if 0 <= delta <= window_seconds:
            msg = "Task '%s' is due %s" % (t["title"], format_date(due))
            sent.append(notify(uid, msg, t["id"]))
            t["reminded"] = True
    return sent
