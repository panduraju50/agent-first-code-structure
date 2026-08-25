# Task due-date reminder.
# When a task is near its due date, notify its assignee.
# Globals `_tasks`, `notify`, `format_date` are wired by layout (see graph.json edges).
REMIND_WINDOW = 86400  # seconds before `due` at which a task counts as "near due" (1 day)
def remind_due(tid, now):
    t = _tasks.get(tid)
    if t is None:
        raise ValueError("no such task")
    if t.get("done"):
        return None            # completed tasks need no reminder
    if t.get("assignee") is None:
        return None            # nobody to notify
    due = t.get("due")
    if due is None:
        return None            # no due date set
    if 0 <= due - now <= REMIND_WINDOW:  # due in the future, within the window
        msg = "Task '" + t["title"] + "' is due " + format_date(due)
        return notify(t["assignee"], msg, tid)
    return None
