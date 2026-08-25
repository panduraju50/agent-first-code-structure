import unittest

from domains.users.service import UserStore


class TestUserStore(unittest.TestCase):
    def test_create_and_get(self):
        store = UserStore()
        user = store.create("alice@example.com")
        self.assertEqual(store.get(user.id), user)

    def test_ids_are_unique(self):
        store = UserStore()
        a = store.create("a@example.com")
        b = store.create("b@example.com")
        self.assertNotEqual(a.id, b.id)

    def test_rejects_email_without_at_sign(self):
        store = UserStore()
        with self.assertRaises(ValueError):
            store.create("not-an-email")

    def test_rejects_email_without_domain(self):
        store = UserStore()
        with self.assertRaises(ValueError):
            store.create("alice@nodot")

    def test_get_missing_raises(self):
        store = UserStore()
        with self.assertRaises(KeyError):
            store.get("does-not-exist")


if __name__ == "__main__":
    unittest.main()
