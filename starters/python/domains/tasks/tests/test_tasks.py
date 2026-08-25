import unittest

from domains.tasks.service import TaskStore


class TestTaskStore(unittest.TestCase):
    def test_create_and_list(self):
        store = TaskStore()
        task = store.create("Ship it")
        self.assertIn(task, store.list())

    def test_ids_are_unique(self):
        store = TaskStore()
        a = store.create("first")
        b = store.create("second")
        self.assertNotEqual(a.id, b.id)

    def test_rejects_empty_title(self):
        store = TaskStore()
        with self.assertRaises(ValueError):
            store.create("   ")

    def test_assign_sets_assignee(self):
        store = TaskStore()
        task = store.create("Ship it")
        updated = store.assign(task.id, "user-123")
        self.assertEqual(updated.assignee_id, "user-123")
        self.assertEqual(store.get(task.id).assignee_id, "user-123")

    def test_assign_missing_raises(self):
        store = TaskStore()
        with self.assertRaises(KeyError):
            store.assign("does-not-exist", "user-123")


if __name__ == "__main__":
    unittest.main()
