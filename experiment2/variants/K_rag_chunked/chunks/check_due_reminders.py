"""@card
purpose: notify a task's assignee when the task is nearing its due date
api: check_due_reminders(now_ts,window_seconds)->list
tags: tasks, notifications, due date, reminder, check due reminders
effects: ['store', 'net']
deps: ['notify']
"""

_reminder_seq = 0  # local counter for notify()'s seq arg; see P1 in notify.py re: collisions

def check_due_reminders(now_ts, window_seconds=86400):
    # Scans all tasks and fires one notification per task that:
    #   - is not done
    #   - has a due_ts set (set_due_date)
    #   - has an assignee (nobody to notify otherwise -- skipped, not an error)
    #   - is within window_seconds of its due date, but not yet past due
    #   - has not already been reminded (task["reminded"] dedupe flag)
    # NOTE: intentionally does NOT cover already-overdue tasks (due_ts < now_ts) --
    # "near its due date" is read as "approaching", not "missed". Flagged in review
    # as a scope choice / possible missing case: overdue tasks currently get no
    # reminder or escalation at all.
    global _reminder_seq
    sent = []
    for t in _tasks.values():
        if t.get("done"):
            continue
        due = t.get("due_ts")
        if due is None:
            continue
        assignee = t.get("assignee")
        if assignee is None:
            continue
        if t.get("reminded"):
            continue
        remaining = due - now_ts
        if 0 <= remaining <= window_seconds:
            _reminder_seq += 1
            note = notify(assignee, "Task '%s' is due soon" % t["title"], _reminder_seq)
            t["reminded"] = True
            sent.append(note)
    return sent
