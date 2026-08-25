_notified = {}
def is_due_soon(due_ts, now_ts, threshold=86400):
    # near-due window: due within [now, now+threshold]. Already-overdue tasks (due_ts < now_ts)
    # are NOT covered here - this module only implements "upcoming due date" reminders, not
    # overdue escalation. That's a real gap (see NOTES in top-level report), left out
    # deliberately rather than silently mis-defining "due soon" to include the past.
    if due_ts is None:
        return False
    delta = due_ts - now_ts
    return 0 <= delta <= threshold


def check_task_reminder(task, now_ts, threshold=86400):
    # Returns the notification dict if a reminder should fire for this task right now,
    # else None. Skips: completed tasks, unassigned tasks, tasks with no due date, tasks
    # not yet within the reminder window, and tasks already reminded for their current
    # due date (dedup via _notified so repeated scans don't spam the assignee).
    tid = task["id"]
    if task.get("done"):
        return None
    if task.get("assignee") is None:
        return None
    due_ts = task.get("due")
    if not is_due_soon(due_ts, now_ts, threshold):
        return None
    if _notified.get(tid) == due_ts:
        return None
    _notified[tid] = due_ts
    msg = "Reminder: task '%s' is due %s" % (task["title"], format_date(due_ts))
    return notify(task["assignee"], msg, tid)


def scan_due_reminders(pid, now_ts, threshold=86400):
    # Sweeps every task in a project and fires reminders where due. Relies on tasks.list_tasks
    # for project scoping, so it inherits that function's behavior as-is (no auth check on the
    # caller either - same gap as the rest of this codebase, see report).
    out = []
    for t in list_tasks(pid):
        n = check_task_reminder(t, now_ts, threshold)
        if n:
            out.append(n)
    return out


def clear_reminder_state(tid):
    # Call this after changing a task's due date so a new reminder can fire for the new date.
    # Not wired automatically from tasks.set_due_date - doing so would make tasks depend on
    # reminders, inverting this layout's dependency direction (tasks is a base module).
    _notified.pop(tid, None)
