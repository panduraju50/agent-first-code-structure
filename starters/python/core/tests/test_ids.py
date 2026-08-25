import unittest

from core.ids import from_base62, new_id, to_base62


class TestBase62(unittest.TestCase):
    def test_roundtrip(self):
        for n in (0, 1, 61, 62, 12345, 999999):
            self.assertEqual(from_base62(to_base62(n)), n)

    def test_zero(self):
        self.assertEqual(to_base62(0), "0")

    def test_rejects_negative(self):
        with self.assertRaises(ValueError):
            to_base62(-1)

    def test_new_id_uses_encoding(self):
        self.assertEqual(new_id(1), to_base62(1))


if __name__ == "__main__":
    unittest.main()
