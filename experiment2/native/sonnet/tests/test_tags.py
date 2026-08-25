import unittest

from taskly import TasklyAPI
from taskly.errors import NotFoundError, ValidationError


class TestTags(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()

    def test_create_tag(self):
        tag = self.api.tags.get_or_create_tag("Bug")
        self.assertTrue(tag.id.startswith("tag_"))
        self.assertEqual(tag.name, "bug")

    def test_get_or_create_dedupes_by_normalized_name(self):
        a = self.api.tags.get_or_create_tag("Bug")
        b = self.api.tags.get_or_create_tag(" bug ")
        c = self.api.tags.get_or_create_tag("BUG")
        self.assertEqual(a.id, b.id)
        self.assertEqual(a.id, c.id)

    def test_different_names_get_different_tags(self):
        a = self.api.tags.get_or_create_tag("bug")
        b = self.api.tags.get_or_create_tag("feature")
        self.assertNotEqual(a.id, b.id)

    def test_empty_name_raises(self):
        with self.assertRaises(ValidationError):
            self.api.tags.get_or_create_tag("   ")

    def test_name_too_long_raises(self):
        with self.assertRaises(ValidationError):
            self.api.tags.get_or_create_tag("x" * 41)

    def test_get_tag_missing_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.tags.get_tag("tag_ghost")

    def test_list_tags_alphabetical(self):
        self.api.tags.get_or_create_tag("zeta")
        self.api.tags.get_or_create_tag("alpha")
        self.api.tags.get_or_create_tag("mid")
        names = [t.name for t in self.api.tags.list_tags()]
        self.assertEqual(names, sorted(names))


if __name__ == "__main__":
    unittest.main()
