"""End-to-end test exercising the full TasklyAPI surface together, the
way an application (or an agent driving the API) actually would.
"""

import unittest

from taskly import TasklyAPI
from taskly.models import TaskStatus


class TestFullWorkflow(unittest.TestCase):
    def test_full_workflow(self):
        api = TasklyAPI()

        # Users + auth.
        ada = api.users.create_user("ada@example.com", "hunter2pass")
        grace = api.users.create_user("grace@example.com", "hunter2pass")
        session = api.users.authenticate("ada@example.com", "hunter2pass")
        self.assertEqual(api.users.get_user_by_session(session.token).id, ada.id)

        # Project + tasks.
        project = api.projects.create_project(ada.id, "Analytical Engine", "Build it")
        task = api.tasks.create_task(
            project.id,
            ada.id,
            "Design the mill",
            description="The arithmetic unit",
            tag_names=["design", "hardware"],
        )
        self.assertEqual(task.status, TaskStatus.OPEN)

        # Assign -> notification.
        api.tasks.assign_task(task.id, grace.id)
        notifications = api.notifications.list_notifications(grace.id)
        self.assertEqual(notifications.total, 1)
        assigned_notification = notifications.items[0]
        self.assertEqual(len(assigned_notification.reference_code), 6)

        # Reference code round-trips to the same notification.
        looked_up = api.notifications.get_by_reference_code(assigned_notification.reference_code)
        self.assertEqual(looked_up.id, assigned_notification.id)

        # Comment by someone other than the assignee notifies the assignee.
        api.comments.add_comment(task.id, ada.id, "How's it going?")
        self.assertEqual(api.notifications.list_notifications(grace.id).total, 2)

        # Search finds the task by title and by description.
        self.assertEqual(api.tasks.search_tasks("mill").total, 1)
        self.assertEqual(api.tasks.search_tasks("arithmetic").total, 1)
        self.assertEqual(api.tasks.search_tasks("nonexistent").total, 0)

        # Complete the task.
        completed = api.tasks.complete_task(task.id)
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(completed.completed_at)

        # Listing tasks reflects final state.
        page = api.tasks.list_tasks(project_id=project.id, status=TaskStatus.COMPLETED)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, task.id)

        # Pagination across a larger set of tasks.
        for i in range(15):
            api.tasks.create_task(project.id, ada.id, f"Bulk task {i}")
        page1 = api.tasks.list_tasks(project_id=project.id, limit=10, offset=0)
        self.assertEqual(len(page1.items), 10)
        self.assertTrue(page1.has_more)
        page2 = api.tasks.list_tasks(project_id=project.id, limit=10, offset=10)
        self.assertEqual(len(page2.items), 6)  # 15 bulk + 1 original = 16 total
        self.assertFalse(page2.has_more)

        # Session revocation ends access.
        api.users.revoke_session(session.token)
        with self.assertRaises(Exception):
            api.users.get_user_by_session(session.token)


if __name__ == "__main__":
    unittest.main()
