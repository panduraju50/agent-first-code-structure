# contract: create_task(pid,title,due_ts=None)->dict  # create a task in a project, optional due date (unix ts)
# contract: list_tasks(pid)->list  # list tasks in a project
# contract: complete_task(tid)->dict  # mark a task done
# contract: assign_task(tid,uid,actor)->dict  # assign a task to a user
# contract: set_due_date(tid,ts)->dict  # set/update a task's due date (unix ts); re-arms its reminder
# contract: check_due_reminders(now_ts,window_seconds=86400)->list  # notify assignees of tasks due within window (not done, not already reminded); returns notifications sent
