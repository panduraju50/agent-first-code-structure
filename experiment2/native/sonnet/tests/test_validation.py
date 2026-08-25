import unittest

from taskly.errors import ValidationError
from taskly.validation import (
    validate_email,
    validate_id,
    validate_non_empty_str,
    validate_optional_str,
    validate_password,
)


class TestValidateEmail(unittest.TestCase):
    def test_valid_email_is_normalized(self):
        self.assertEqual(validate_email("  Ada@Example.COM "), "ada@example.com")

    def test_missing_at_raises(self):
        with self.assertRaises(ValidationError):
            validate_email("not-an-email")

    def test_missing_domain_dot_raises(self):
        with self.assertRaises(ValidationError):
            validate_email("ada@example")

    def test_empty_raises(self):
        with self.assertRaises(ValidationError):
            validate_email("   ")

    def test_non_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_email(123)

    def test_too_long_raises(self):
        long_local = "a" * 250
        with self.assertRaises(ValidationError):
            validate_email(f"{long_local}@example.com")

    def test_none_raises(self):
        with self.assertRaises(ValidationError):
            validate_email(None)


class TestValidatePassword(unittest.TestCase):
    def test_valid_password_passes(self):
        self.assertEqual(validate_password("hunter2pass"), "hunter2pass")

    def test_too_short_raises(self):
        with self.assertRaises(ValidationError):
            validate_password("short1")

    def test_too_long_raises(self):
        with self.assertRaises(ValidationError):
            validate_password("x" * 129)

    def test_non_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_password(12345678)

    def test_password_not_trimmed(self):
        # Whitespace is significant in a password; must round-trip exactly.
        self.assertEqual(validate_password("  spaced "), "  spaced ")


class TestValidateNonEmptyStr(unittest.TestCase):
    def test_trims_and_returns(self):
        self.assertEqual(validate_non_empty_str("  hi  ", "field"), "hi")

    def test_empty_after_trim_raises(self):
        with self.assertRaises(ValidationError):
            validate_non_empty_str("   ", "field")

    def test_non_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_non_empty_str(42, "field")

    def test_over_max_length_raises(self):
        with self.assertRaises(ValidationError):
            validate_non_empty_str("abcdef", "field", max_length=3)

    def test_at_max_length_ok(self):
        self.assertEqual(validate_non_empty_str("abc", "field", max_length=3), "abc")


class TestValidateOptionalStr(unittest.TestCase):
    def test_none_passes_through(self):
        self.assertIsNone(validate_optional_str(None, "field"))

    def test_string_is_trimmed(self):
        self.assertEqual(validate_optional_str("  hi  ", "field"), "hi")

    def test_over_max_length_raises(self):
        with self.assertRaises(ValidationError):
            validate_optional_str("abcdef", "field", max_length=3)

    def test_non_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_optional_str(42, "field")


class TestValidateId(unittest.TestCase):
    def test_valid_id_passes(self):
        self.assertEqual(validate_id("usr_abc123", "user_id"), "usr_abc123")

    def test_none_raises(self):
        with self.assertRaises(ValidationError):
            validate_id(None, "user_id")

    def test_empty_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_id("   ", "user_id")

    def test_non_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_id(123, "user_id")


if __name__ == "__main__":
    unittest.main()
