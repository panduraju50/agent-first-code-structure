import time
def send_due_date_reminders(reminder_threshold_seconds=86400):
    """
    Send notifications to assignees for tasks approaching their due date.
    reminder_threshold_seconds: how many seconds until due date triggers a reminder (default: 1 day)
    Returns list of notifications sent
    """
    current_time = int(time.time())
    notifications_sent = []
    seq_counter = len(_tasks) + 1

    for task in _tasks.values():
        # Skip tasks without due_date, without assignee, or already completed
        if not task.get("due_date") or task.get("assignee") is None or task.get("done"):
            continue

        # Check if task is within reminder window
        time_until_due = task["due_date"] - current_time
        if 0 <= time_until_due <= reminder_threshold_seconds:
            assignee_id = task["assignee"]
            msg = f"Task '{task['title']}' (ID: {task['id']}) is due soon on {format_date(task['due_date'])}"
            notification = notify(assignee_id, msg, seq_counter)
            notifications_sent.append(notification)
            seq_counter += 1

    return notifications_sent
