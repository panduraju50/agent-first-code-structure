def check_due_date_reminder(current_time, days_threshold=1):
    # Check all tasks and send reminders for tasks nearing their due date
    # current_time: timestamp (seconds since epoch)
    # days_threshold: how many days before due date to send reminder (default 1)
    reminders = []
    threshold_seconds = days_threshold * 86400

    for task in _tasks.values():
        # Skip tasks that are done or don't have an assignee or due date
        if task["done"] or task["assignee"] is None or task["due_date"] is None:
            continue

        # Parse the due date
        due_date_ts = int(task["due_date"].replace("day-", "")) * 86400
        time_until_due = due_date_ts - current_time

        # If task is overdue or within threshold, send reminder
        if 0 <= time_until_due <= threshold_seconds:
            notification = notify(task["assignee"],
                                f"Task '{task['title']}' is due soon",
                                task["id"])
            reminders.append(notification)

    return reminders
