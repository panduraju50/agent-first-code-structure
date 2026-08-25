import unittest

from core.validation import validate_email, validate_title


class TestValidateTitle(unittest.TestCase):
    def test_accepts_and_strips(self):
        self.assertEqual(validate_title("  hello  "), "hello")

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            validate_title("   ")

    def test_rejects_none(self):
        with self.assertRaises(ValueError):
            validate_title(None)


class TestValidateEmail(unittest.TestCase):
    def test_accepts_valid(self):
        self.assertEqual(validate_email("a@b.com"), "a@b.com")

    def test_requires_at_sign(self):
        with self.assertRaises(ValueError):
            validate_email("a-b.com")

    def test_requires_domain(self):
        with self.assertRaises(ValueError):
            validate_email("a@b")


if __name__ == "__main__":
    unittest.main()
