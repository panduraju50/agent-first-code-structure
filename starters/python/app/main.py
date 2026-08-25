"""Composition root.

This is the ONLY module in the repo allowed to import more than one
domain. It wires domains.users and domains.tasks together and owns the
cross-domain rule ("assigning a task to a user requires that user to
exist") that neither domain is allowed to encode itself.
"""

from domains.tasks.service import TaskStore
from domains.users.service import UserStore


def assign_task(users: UserStore, tasks: TaskStore, task_id: str, user_id: str):
    """Cross-domain operation: lives here, not inside either domain."""
    users.get(user_id)  # raises KeyError if the user doesn't exist
    return tasks.assign(task_id, user_id)


def run_scenario():
    users = UserStore()
    tasks = TaskStore()

    alice = users.create("alice@example.com")
    bob = users.create("bob@example.com")

    t1 = tasks.create("Write the Design D README")
    t2 = tasks.create("Wire the boundary enforcer into CI")

    assign_task(users, tasks, t1.id, alice.id)
    assign_task(users, tasks, t2.id, bob.id)

    print("Users:")
    for u in (alice, bob):
        print(f"  {u.id}  {u.email}")

    print("Tasks:")
    for t in tasks.list():
        print(f"  {t.id}  {t.title!r}  assignee={t.assignee_id}")

    return {"users": [alice, bob], "tasks": tasks.list()}


if __name__ == "__main__":
    run_scenario()
