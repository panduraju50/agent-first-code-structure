import unittest

from taskly.errors import NotFoundError
from taskly.store import Repository, TasklyStore


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.repo = Repository("widget")

    def test_save_and_get(self):
        self.repo.save("w1", {"name": "a"})
        self.assertEqual(self.repo.get("w1"), {"name": "a"})

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.repo.get("missing"))

    def test_require_missing_raises_named_error(self):
        with self.assertRaises(NotFoundError) as ctx:
            self.repo.require("missing")
        self.assertIn("widget", str(ctx.exception))
        self.assertIn("missing", str(ctx.exception))

    def test_delete(self):
        self.repo.save("w1", {"name": "a"})
        self.repo.delete("w1")
        self.assertIsNone(self.repo.get("w1"))

    def test_delete_missing_is_noop(self):
        self.repo.delete("never-existed")  # must not raise

    def test_all_and_len(self):
        self.repo.save("w1", 1)
        self.repo.save("w2", 2)
        self.assertEqual(len(self.repo), 2)
        self.assertEqual(sorted(self.repo.all()), [1, 2])

    def test_filter(self):
        self.repo.save("w1", 1)
        self.repo.save("w2", 2)
        self.repo.save("w3", 3)
        self.assertEqual(sorted(self.repo.filter(lambda x: x % 2 == 1)), [1, 3])

    def test_exists(self):
        self.repo.save("w1", 1)
        self.assertTrue(self.repo.exists("w1"))
        self.assertFalse(self.repo.exists("w2"))


class TestTasklyStoreIsolation(unittest.TestCase):
    def test_two_stores_are_independent(self):
        a = TasklyStore()
        b = TasklyStore()
        a.users.save("u1", "alice")
        self.assertIsNone(b.users.get("u1"))
        self.assertEqual(len(a.users), 1)
        self.assertEqual(len(b.users), 0)


if __name__ == "__main__":
    unittest.main()
