import unittest

from taskly import TasklyAPI
from taskly.errors import AuthError, ConflictError, NotFoundError, ValidationError


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()

    def test_create_user_success(self):
        user = self.api.users.create_user("ada@example.com", "hunter2pass")
        self.assertTrue(user.id.startswith("usr_"))
        self.assertEqual(user.email, "ada@example.com")
        self.assertNotEqual(user.password_hash, "hunter2pass")

    def test_email_is_normalized(self):
        user = self.api.users.create_user("  Ada@Example.COM ", "hunter2pass")
        self.assertEqual(user.email, "ada@example.com")

    def test_duplicate_email_raises_conflict(self):
        self.api.users.create_user("ada@example.com", "hunter2pass")
        with self.assertRaises(ConflictError):
            self.api.users.create_user("ada@example.com", "differentpass")

    def test_duplicate_email_case_insensitive(self):
        self.api.users.create_user("ada@example.com", "hunter2pass")
        with self.assertRaises(ConflictError):
            self.api.users.create_user("ADA@EXAMPLE.COM", "differentpass")

    def test_invalid_email_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.users.create_user("not-an-email", "hunter2pass")

    def test_short_password_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.users.create_user("ada@example.com", "short")


class TestGetUser(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.user = self.api.users.create_user("ada@example.com", "hunter2pass")

    def test_get_by_id(self):
        self.assertEqual(self.api.users.get_user(self.user.id).id, self.user.id)

    def test_get_by_id_missing_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.users.get_user("usr_doesnotexist")

    def test_get_by_email(self):
        self.assertEqual(self.api.users.get_user_by_email("ada@example.com").id, self.user.id)

    def test_get_by_email_missing_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.users.get_user_by_email("nobody@example.com")


class TestAuthenticate(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.user = self.api.users.create_user("ada@example.com", "hunter2pass")

    def test_correct_credentials_returns_session(self):
        session = self.api.users.authenticate("ada@example.com", "hunter2pass")
        self.assertEqual(session.user_id, self.user.id)
        self.assertTrue(session.token)

    def test_wrong_password_raises_autherror(self):
        with self.assertRaises(AuthError):
            self.api.users.authenticate("ada@example.com", "wrongpassword")

    def test_unknown_email_raises_autherror(self):
        with self.assertRaises(AuthError):
            self.api.users.authenticate("nobody@example.com", "hunter2pass")

    def test_unknown_email_and_wrong_password_same_error_message(self):
        # Guards against a user-enumeration regression: both failure modes
        # must be indistinguishable to the caller.
        try:
            self.api.users.authenticate("nobody@example.com", "hunter2pass")
            self.fail("expected AuthError")
        except AuthError as e:
            msg_unknown_user = str(e)
        try:
            self.api.users.authenticate("ada@example.com", "wrongpassword")
            self.fail("expected AuthError")
        except AuthError as e:
            msg_wrong_password = str(e)
        self.assertEqual(msg_unknown_user, msg_wrong_password)

    def test_session_resolves_to_user(self):
        session = self.api.users.authenticate("ada@example.com", "hunter2pass")
        resolved = self.api.users.get_user_by_session(session.token)
        self.assertEqual(resolved.id, self.user.id)

    def test_invalid_token_raises_autherror(self):
        with self.assertRaises(AuthError):
            self.api.users.get_user_by_session("not-a-real-token")

    def test_revoke_session_invalidates_it(self):
        session = self.api.users.authenticate("ada@example.com", "hunter2pass")
        self.api.users.revoke_session(session.token)
        with self.assertRaises(AuthError):
            self.api.users.get_user_by_session(session.token)

    def test_revoke_unknown_token_is_noop(self):
        self.api.users.revoke_session("never-issued-token")  # must not raise

    def test_expired_session_raises_and_is_evicted(self):
        session = self.api.users.authenticate("ada@example.com", "hunter2pass")
        # Force expiry.
        self.api.store.sessions[session.token].expires_at = 0
        with self.assertRaises(AuthError):
            self.api.users.get_user_by_session(session.token)
        self.assertNotIn(session.token, self.api.store.sessions)


if __name__ == "__main__":
    unittest.main()
