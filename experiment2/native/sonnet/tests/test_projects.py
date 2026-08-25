import unittest

from taskly import TasklyAPI
from taskly.errors import NotFoundError, ValidationError


class TestCreateProject(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.user = self.api.users.create_user("ada@example.com", "hunter2pass")

    def test_create_project_success(self):
        project = self.api.projects.create_project(self.user.id, "Analytical Engine", "desc")
        self.assertTrue(project.id.startswith("prj_"))
        self.assertEqual(project.owner_id, self.user.id)
        self.assertEqual(project.name, "Analytical Engine")
        self.assertEqual(project.description, "desc")

    def test_create_project_without_description(self):
        project = self.api.projects.create_project(self.user.id, "No Description")
        self.assertIsNone(project.description)

    def test_unknown_owner_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.api.projects.create_project("usr_ghost", "Ghost Project")

    def test_empty_name_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.projects.create_project(self.user.id, "   ")

    def test_name_too_long_raises(self):
        with self.assertRaises(ValidationError):
            self.api.projects.create_project(self.user.id, "x" * 141)


class TestGetProject(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.user = self.api.users.create_user("ada@example.com", "hunter2pass")
        self.project = self.api.projects.create_project(self.user.id, "P1")

    def test_get_project(self):
        self.assertEqual(self.api.projects.get_project(self.project.id).id, self.project.id)

    def test_get_missing_project_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.projects.get_project("prj_ghost")


class TestListProjects(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.alice = self.api.users.create_user("alice@example.com", "hunter2pass")
        self.bob = self.api.users.create_user("bob@example.com", "hunter2pass")
        for i in range(3):
            self.api.projects.create_project(self.alice.id, f"Alice Project {i}")
        for i in range(2):
            self.api.projects.create_project(self.bob.id, f"Bob Project {i}")

    def test_list_all(self):
        page = self.api.projects.list_projects()
        self.assertEqual(page.total, 5)

    def test_list_scoped_to_owner(self):
        page = self.api.projects.list_projects(owner_id=self.alice.id)
        self.assertEqual(page.total, 3)
        self.assertTrue(all(p.owner_id == self.alice.id for p in page.items))

    def test_list_pagination(self):
        page = self.api.projects.list_projects(owner_id=self.alice.id, limit=2, offset=0)
        self.assertEqual(len(page.items), 2)
        self.assertTrue(page.has_more)
        page2 = self.api.projects.list_projects(owner_id=self.alice.id, limit=2, offset=2)
        self.assertEqual(len(page2.items), 1)
        self.assertFalse(page2.has_more)

    def test_list_ordered_oldest_first(self):
        page = self.api.projects.list_projects(owner_id=self.alice.id)
        created_ats = [p.created_at for p in page.items]
        self.assertEqual(created_ats, sorted(created_ats))

    def test_list_owner_with_no_projects_empty(self):
        stranger = self.api.users.create_user("stranger@example.com", "hunter2pass")
        page = self.api.projects.list_projects(owner_id=stranger.id)
        self.assertEqual(page.total, 0)
        self.assertEqual(page.items, [])


if __name__ == "__main__":
    unittest.main()
