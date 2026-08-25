import unittest

from taskly import ids


class TestIds(unittest.TestCase):
    def test_new_id_has_prefix_and_body(self):
        value = ids.new_id("usr")
        self.assertTrue(value.startswith("usr_"))
        body = value[len("usr_"):]
        self.assertEqual(len(body), ids.DEFAULT_ID_LENGTH)
        self.assertTrue(all(c in ids._ALPHABET for c in body))

    def test_new_id_without_prefix_has_no_underscore(self):
        value = ids.new_id()
        self.assertNotIn("_", value)
        self.assertEqual(len(value), ids.DEFAULT_ID_LENGTH)

    def test_new_id_is_random(self):
        values = {ids.new_id("x") for _ in range(200)}
        self.assertEqual(len(values), 200)

    def test_new_reference_code_length_and_charset(self):
        code = ids.new_reference_code()
        self.assertEqual(len(code), ids.DEFAULT_REFERENCE_CODE_LENGTH)
        self.assertTrue(all(c in ids._ALPHABET for c in code))

    def test_new_reference_code_custom_length(self):
        code = ids.new_reference_code(10)
        self.assertEqual(len(code), 10)

    def test_encode_decode_base62_roundtrip(self):
        for n in (0, 1, 61, 62, 63, 12345, 999999999):
            self.assertEqual(ids.decode_base62(ids.encode_base62(n)), n)

    def test_encode_base62_zero(self):
        self.assertEqual(ids.encode_base62(0), "0")

    def test_encode_base62_negative_raises(self):
        with self.assertRaises(ValueError):
            ids.encode_base62(-1)

    def test_decode_base62_invalid_char_raises(self):
        with self.assertRaises(ValueError):
            ids.decode_base62("!!!")


if __name__ == "__main__":
    unittest.main()
