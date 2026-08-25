import unittest

from taskly.errors import ValidationError
from taskly.pagination import MAX_LIMIT, paginate, validate_pagination


class TestValidatePagination(unittest.TestCase):
    def test_defaults_ok(self):
        self.assertEqual(validate_pagination(), (20, 0))

    def test_zero_limit_raises(self):
        with self.assertRaises(ValidationError):
            validate_pagination(limit=0)

    def test_negative_limit_raises(self):
        with self.assertRaises(ValidationError):
            validate_pagination(limit=-1)

    def test_limit_over_max_raises(self):
        with self.assertRaises(ValidationError):
            validate_pagination(limit=MAX_LIMIT + 1)

    def test_limit_at_max_ok(self):
        self.assertEqual(validate_pagination(limit=MAX_LIMIT), (MAX_LIMIT, 0))

    def test_negative_offset_raises(self):
        with self.assertRaises(ValidationError):
            validate_pagination(offset=-1)

    def test_bool_limit_rejected(self):
        with self.assertRaises(ValidationError):
            validate_pagination(limit=True)

    def test_bool_offset_rejected(self):
        with self.assertRaises(ValidationError):
            validate_pagination(offset=False)

    def test_non_int_limit_rejected(self):
        with self.assertRaises(ValidationError):
            validate_pagination(limit="10")


class TestPaginate(unittest.TestCase):
    def test_first_page(self):
        page = paginate(list(range(25)), limit=10, offset=0)
        self.assertEqual(page.items, list(range(10)))
        self.assertEqual(page.total, 25)
        self.assertTrue(page.has_more)
        self.assertEqual(page.next_offset, 10)

    def test_last_page_partial(self):
        page = paginate(list(range(25)), limit=10, offset=20)
        self.assertEqual(page.items, list(range(20, 25)))
        self.assertFalse(page.has_more)
        self.assertIsNone(page.next_offset)

    def test_offset_beyond_total(self):
        page = paginate(list(range(5)), limit=10, offset=50)
        self.assertEqual(page.items, [])
        self.assertEqual(page.total, 5)
        self.assertFalse(page.has_more)

    def test_empty_items(self):
        page = paginate([], limit=10, offset=0)
        self.assertEqual(page.items, [])
        self.assertEqual(page.total, 0)
        self.assertFalse(page.has_more)

    def test_exact_boundary_no_more(self):
        page = paginate(list(range(10)), limit=10, offset=0)
        self.assertFalse(page.has_more)


if __name__ == "__main__":
    unittest.main()
