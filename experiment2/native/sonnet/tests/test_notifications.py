import unittest

from taskly import TasklyAPI
from taskly.errors import NotFoundError, ValidationError


class TasklyTestCase(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.alice = self.api.users.create_user("alice@example.com", "hunter2pass")


class TestCreateNotification(TasklyTestCase):
    def test_create_notification_has_reference_code(self):
        n = self.api.notifications.create_notification(self.alice.id, "test_kind", "hello")
        self.assertTrue(n.id.startswith("ntf_"))
        self.assertEqual(len(n.reference_code), 6)
        self.assertFalse(n.read)

    def test_reference_codes_are_unique(self):
        codes = set()
        for i in range(50):
            n = self.api.notifications.create_notification(self.alice.id, "kind", f"msg {i}")
            codes.add(n.reference_code)
        self.assertEqual(len(codes), 50)

    def test_unknown_user_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.api.notifications.create_notification("usr_ghost", "kind", "msg")

    def test_empty_message_raises(self):
        with self.assertRaises(ValidationError):
            self.api.notifications.create_notification(self.alice.id, "kind", "   ")


class TestGetByReferenceCode(TasklyTestCase):
    def test_lookup_by_reference_code(self):
        n = self.api.notifications.create_notification(self.alice.id, "kind", "msg")
        found = self.api.notifications.get_by_reference_code(n.reference_code)
        self.assertEqual(found.id, n.id)

    def test_lookup_is_case_insensitive(self):
        n = self.api.notifications.create_notification(self.alice.id, "kind", "msg")
        found = self.api.notifications.get_by_reference_code(n.reference_code.lower())
        self.assertEqual(found.id, n.id)

    def test_unknown_reference_code_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.notifications.get_by_reference_code("ZZZZZZ")


class TestListNotifications(TasklyTestCase):
    def setUp(self):
        super().setUp()
        self.n1 = self.api.notifications.create_notification(self.alice.id, "kind", "first")
        self.n2 = self.api.notifications.create_notification(self.alice.id, "kind", "second")

    def test_list_newest_first(self):
        page = self.api.notifications.list_notifications(self.alice.id)
        self.assertEqual([n.id for n in page.items], [self.n2.id, self.n1.id])

    def test_unread_only_filter(self):
        self.api.notifications.mark_read(self.n1.id)
        page = self.api.notifications.list_notifications(self.alice.id, unread_only=True)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.n2.id)

    def test_mark_read(self):
        updated = self.api.notifications.mark_read(self.n1.id)
        self.assertTrue(updated.read)

    def test_mark_read_missing_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.notifications.mark_read("ntf_ghost")


if __name__ == "__main__":
    unittest.main()
