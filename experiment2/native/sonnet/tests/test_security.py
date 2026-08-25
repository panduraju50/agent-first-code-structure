import time
import unittest

from taskly.security import Session, hash_password, new_session_token, verify_password


class TestPasswordHashing(unittest.TestCase):
    def test_verify_correct_password(self):
        encoded = hash_password("hunter2pass")
        self.assertTrue(verify_password("hunter2pass", encoded))

    def test_verify_wrong_password_fails(self):
        encoded = hash_password("hunter2pass")
        self.assertFalse(verify_password("wrongpassword", encoded))

    def test_hash_is_salted_differently_each_time(self):
        a = hash_password("samepassword")
        b = hash_password("samepassword")
        self.assertNotEqual(a, b)
        self.assertTrue(verify_password("samepassword", a))
        self.assertTrue(verify_password("samepassword", b))

    def test_hash_does_not_contain_plaintext(self):
        encoded = hash_password("supersecretvalue")
        self.assertNotIn("supersecretvalue", encoded)

    def test_verify_malformed_hash_returns_false(self):
        self.assertFalse(verify_password("anything", "not-a-valid-hash"))

    def test_verify_wrong_algorithm_tag_returns_false(self):
        self.assertFalse(verify_password("x", "bcrypt$10$abc$def"))

    def test_verify_non_hex_returns_false(self):
        self.assertFalse(verify_password("x", "pbkdf2_sha256$200000$zzzz$zzzz"))


class TestSessionToken(unittest.TestCase):
    def test_tokens_are_unique(self):
        tokens = {new_session_token() for _ in range(50)}
        self.assertEqual(len(tokens), 50)

    def test_session_not_expired_when_fresh(self):
        s = Session(token="t", user_id="u1", created_at=time.time(), expires_at=time.time() + 100)
        self.assertFalse(s.is_expired())

    def test_session_expired_after_expiry(self):
        now = time.time()
        s = Session(token="t", user_id="u1", created_at=now - 200, expires_at=now - 100)
        self.assertTrue(s.is_expired())

    def test_session_expired_uses_explicit_now(self):
        s = Session(token="t", user_id="u1", created_at=0, expires_at=100)
        self.assertFalse(s.is_expired(now=50))
        self.assertTrue(s.is_expired(now=150))


if __name__ == "__main__":
    unittest.main()
