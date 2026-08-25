import unittest

from taskly import TasklyAPI
from taskly.errors import NotFoundError, ValidationError
from taskly.models import TaskStatus


class TasklyTestCase(unittest.TestCase):
    def setUp(self):
        self.api = TasklyAPI()
        self.alice = self.api.users.create_user("alice@example.com", "hunter2pass")
        self.bob = self.api.users.create_user("bob@example.com", "hunter2pass")
        self.project = self.api.projects.create_project(self.alice.id, "Project")


class TestCreateTask(TasklyTestCase):
    def test_create_task_success(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "Write tests")
        self.assertTrue(task.id.startswith("tsk_"))
        self.assertEqual(task.status, TaskStatus.OPEN)
        self.assertIsNone(task.assignee_id)
        self.assertIsNone(task.completed_at)

    def test_create_task_with_assignee_notifies(self):
        task = self.api.tasks.create_task(
            self.project.id, self.alice.id, "Write tests", assignee_id=self.bob.id
        )
        self.assertEqual(task.assignee_id, self.bob.id)
        page = self.api.notifications.list_notifications(self.bob.id)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].kind, "task_assigned")

    def test_create_task_with_tags(self):
        task = self.api.tasks.create_task(
            self.project.id, self.alice.id, "Write tests", tag_names=["bug", "Bug", "urgent"]
        )
        # "bug" and "Bug" dedupe to one tag id.
        self.assertEqual(len(task.tag_ids), 2)

    def test_unknown_project_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.api.tasks.create_task("prj_ghost", self.alice.id, "Title")

    def test_unknown_creator_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.api.tasks.create_task(self.project.id, "usr_ghost", "Title")

    def test_unknown_assignee_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.api.tasks.create_task(
                self.project.id, self.alice.id, "Title", assignee_id="usr_ghost"
            )

    def test_empty_title_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            self.api.tasks.create_task(self.project.id, self.alice.id, "   ")


class TestCompleteTask(TasklyTestCase):
    def test_complete_task_sets_status_and_timestamp(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        completed = self.api.tasks.complete_task(task.id)
        self.assertEqual(completed.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(completed.completed_at)

    def test_complete_is_idempotent(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        first = self.api.tasks.complete_task(task.id)
        first_completed_at = first.completed_at
        second = self.api.tasks.complete_task(task.id)
        self.assertEqual(second.completed_at, first_completed_at)

    def test_complete_missing_task_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.tasks.complete_task("tsk_ghost")


class TestAssignTask(TasklyTestCase):
    def test_assign_task_success(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        assigned = self.api.tasks.assign_task(task.id, self.bob.id)
        self.assertEqual(assigned.assignee_id, self.bob.id)

    def test_assign_notifies_new_assignee(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        self.api.tasks.assign_task(task.id, self.bob.id)
        page = self.api.notifications.list_notifications(self.bob.id)
        self.assertEqual(page.total, 1)

    def test_assign_to_unknown_user_raises(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        with self.assertRaises(NotFoundError):
            self.api.tasks.assign_task(task.id, "usr_ghost")

    def test_reassign_notifies_each_time(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        self.api.tasks.assign_task(task.id, self.bob.id)
        self.api.tasks.assign_task(task.id, self.alice.id)
        self.assertEqual(self.api.notifications.list_notifications(self.bob.id).total, 1)
        self.assertEqual(self.api.notifications.list_notifications(self.alice.id).total, 1)


class TestListTasks(TasklyTestCase):
    def setUp(self):
        super().setUp()
        self.project2 = self.api.projects.create_project(self.alice.id, "Project 2")
        self.t1 = self.api.tasks.create_task(self.project.id, self.alice.id, "T1", assignee_id=self.bob.id)
        self.t2 = self.api.tasks.create_task(self.project.id, self.alice.id, "T2")
        self.t3 = self.api.tasks.create_task(self.project2.id, self.alice.id, "T3")
        self.api.tasks.complete_task(self.t2.id)

    def test_list_all(self):
        self.assertEqual(self.api.tasks.list_tasks().total, 3)

    def test_filter_by_project(self):
        page = self.api.tasks.list_tasks(project_id=self.project.id)
        self.assertEqual(page.total, 2)

    def test_filter_by_status(self):
        page = self.api.tasks.list_tasks(status=TaskStatus.COMPLETED)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.t2.id)

    def test_filter_by_assignee(self):
        page = self.api.tasks.list_tasks(assignee_id=self.bob.id)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.t1.id)

    def test_combined_filters(self):
        page = self.api.tasks.list_tasks(project_id=self.project.id, status=TaskStatus.OPEN)
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.t1.id)

    def test_ordered_oldest_first(self):
        page = self.api.tasks.list_tasks(project_id=self.project.id)
        self.assertEqual([t.id for t in page.items], [self.t1.id, self.t2.id])


class TestSearchTasks(TasklyTestCase):
    def setUp(self):
        super().setUp()
        self.t1 = self.api.tasks.create_task(self.project.id, self.alice.id, "Fix login bug")
        self.t2 = self.api.tasks.create_task(
            self.project.id, self.alice.id, "Add export", description="CSV export for reports"
        )
        self.t3 = self.api.tasks.create_task(self.project.id, self.alice.id, "Unrelated task")

    def test_search_matches_title(self):
        page = self.api.tasks.search_tasks("login")
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.t1.id)

    def test_search_matches_description(self):
        page = self.api.tasks.search_tasks("csv")
        self.assertEqual(page.total, 1)
        self.assertEqual(page.items[0].id, self.t2.id)

    def test_search_is_case_insensitive(self):
        page = self.api.tasks.search_tasks("BUG")
        self.assertEqual(page.total, 1)

    def test_search_no_match(self):
        page = self.api.tasks.search_tasks("nonexistentword")
        self.assertEqual(page.total, 0)

    def test_search_scoped_to_project(self):
        other_project = self.api.projects.create_project(self.alice.id, "Other")
        self.api.tasks.create_task(other_project.id, self.alice.id, "login page in other project")
        page = self.api.tasks.search_tasks("login", project_id=self.project.id)
        self.assertEqual(page.total, 1)

    def test_search_empty_query_raises(self):
        with self.assertRaises(ValidationError):
            self.api.tasks.search_tasks("   ")


class TestAddTags(TasklyTestCase):
    def test_add_tags_to_existing_task(self):
        task = self.api.tasks.create_task(self.project.id, self.alice.id, "T")
        self.api.tasks.add_tags(task.id, ["bug", "urgent"])
        refreshed = self.api.tasks.get_task(task.id)
        self.assertEqual(len(refreshed.tag_ids), 2)

    def test_add_tags_missing_task_raises(self):
        with self.assertRaises(NotFoundError):
            self.api.tasks.add_tags("tsk_ghost", ["bug"])


if __name__ == "__main__":
    unittest.main()
