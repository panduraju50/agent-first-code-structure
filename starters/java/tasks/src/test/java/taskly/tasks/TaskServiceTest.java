package taskly.tasks;

import java.util.List;

/**
 * Plain-Java test (no framework, no network install): a main() with checks
 * that exits non-zero on the first failure. Run via test.sh / `make test`.
 */
public final class TaskServiceTest {

    private static int failures = 0;

    public static void main(String[] args) {
        createAssignsBase62IdAndStoresTask();
        listReturnsAllCreatedTasks();
        assignSetsAssigneeId();
        createRejectsBlankTitle();

        if (failures > 0) {
            System.out.println("FAIL: " + failures + " check(s) failed in TaskServiceTest");
            System.exit(1);
        }
        System.out.println("PASS: TaskServiceTest");
    }

    private static void createAssignsBase62IdAndStoresTask() {
        TaskService service = new TaskService();
        Task task = service.create("Write the README");
        check("id is non-empty", task.id() != null && !task.id().isEmpty());
        check("title preserved", task.title().equals("Write the README"));
        check("no assignee yet", task.assigneeId() == null);
        check("get roundtrips", service.get(task.id()).orElseThrow().equals(task));
    }

    private static void listReturnsAllCreatedTasks() {
        TaskService service = new TaskService();
        service.create("First");
        service.create("Second");
        List<Task> tasks = service.list();
        check("list has two tasks", tasks.size() == 2);
        check("first task title", tasks.get(0).title().equals("First"));
        check("second task title", tasks.get(1).title().equals("Second"));
    }

    private static void assignSetsAssigneeId() {
        TaskService service = new TaskService();
        Task task = service.create("Ship it");
        // assigneeId is a plain String — this module has no taskly.users type.
        Task updated = service.assign(task.id(), "user-42");
        check("assignee set", "user-42".equals(updated.assigneeId()));
        check("get reflects assignment",
                "user-42".equals(service.get(task.id()).orElseThrow().assigneeId()));
    }

    private static void createRejectsBlankTitle() {
        TaskService service = new TaskService();
        try {
            service.create("");
            check("blank title should have thrown", false);
        } catch (IllegalArgumentException expected) {
            check("blank title throws IllegalArgumentException", true);
        }
    }

    private static void check(String description, boolean condition) {
        if (condition) {
            System.out.println("  ok - " + description);
        } else {
            System.out.println("  NOT OK - " + description);
            failures++;
        }
    }
}
