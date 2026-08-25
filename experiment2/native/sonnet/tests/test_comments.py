import unittest

from taskly import TasklyAPI
from taskly.errors import NotFoundError, ValidationError


class TasklyTestCase(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.alice = self.api.users.create_user("alice@example.com", "hunter2pass")
        self.bob = self.api.users.create_user("bob@example.com", "hunter2pass")
        self.project = self.api.projects.create_project(self.alice.id, "Project")
        self.task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")


class TestAddComment(TasklyTestCase):
    def test_add_comment_success(self):
        comment = self.api.comments.add_comment(self.task.id, self.alice.id, "Looks good")
        self.assertTrue(comment.id.startswith("cmt_"))
        self.assertEqual(comment.body, "Looks good")

    def test_add_comment_unknown_task_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.comments.add_comment("tsk_ghost", self.alice.id, "hi")

    def test_add_comment_unknown_author_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.comments.add_comment(self.task.id, "usr_ghost", "hi")

    def test_empty_body_raises(self):
        with self.assertRaises(ValidationError):
            self.api.comments.add_comment(self.task.id, self.alice.id, "   ")

    def test_comment_notifies_assignee(self):
        self.api.tasks.assign_task(self.task.id, self.bob.id)
        self.api.notifications.list_notifications(self.bob.id)  # drain assignment notif count first
        before = self.api.notifications.list_notifications(self.bob.id).total
        self.api.comments.add_comment(self.task.id, self.alice.id, "hello")
        after = self.api.notifications.list_notifications(self.bob.id).total
        self.assertEqual(after, before + 1)

    def test_comment_by_assignee_on_own_task_does_not_self_notify(self):
        self.api.tasks.assign_task(self.task.id, self.bob.id)
        before = self.api.notifications.list_notifications(self.bob.id).total
        self.api.comments.add_comment(self.task.id, self.bob.id, "I'm on it")
        after = self.api.notifications.list_notifications(self.bob.id).total
        self.assertEqual(after, before)

    def test_comment_on_unassigned_task_does_not_notify_anyone(self):
        self.api.comments.add_comment(self.task.id, self.alice.id, "no assignee yet")
        self.assertEqual(self.api.notifications.list_notifications(self.alice.id).total, 0)
        self.assertEqual(self.api.notifications.list_notifications(self.bob.id).total, 0)


class TestListComments(TasklyTestCase):
    def test_list_comments_chronological(self):
        c1 = self.api.comments.add_comment(self.task.id, self.alice.id, "first")
        c2 = self.api.comments.add_comment(self.task.id, self.bob.id, "second")
        page = self.api.comments.list_comments(self.task.id)
        self.assertEqual([c.id for c in page.items], [c1.id, c2.id])

    def test_list_comments_missing_task_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.comments.list_comments("tsk_ghost")

    def test_list_comments_empty(self):
        page = self.api.comments.list_comments(self.task.id)
        self.assertEqual(page.total, 0)


if __name__ == "__main__":
    unittest.main()
