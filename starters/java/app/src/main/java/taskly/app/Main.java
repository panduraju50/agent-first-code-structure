package taskly.app;

import java.util.List;

import taskly.tasks.Task;
import taskly.tasks.TaskService;
import taskly.users.User;
import taskly.users.UserService;

/**
 * Composition root: this is the only file in the repo that imports from
 * both taskly.users and taskly.tasks. It wires the two domains together at
 * the value level (an assignee id passed from one service to the other) —
 * never at the type level — and runs a tiny end-to-end scenario.
 */
public final class Main {

    public static void main(String[] args) {
        UserService users = new UserService();
        TaskService tasks = new TaskService();

        User ada = users.create("Ada Lovelace", "ada@example.com");
        User grace = users.create("Grace Hopper", "grace@example.com");
        System.out.println("created user: " + ada);
        System.out.println("created user: " + grace);

        Task readme = tasks.create("Write the README");
        Task boundary = tasks.create("Wire up the boundary checker");
        System.out.println("created task: " + readme);
        System.out.println("created task: " + boundary);

        tasks.assign(readme.id(), ada.id());
        tasks.assign(boundary.id(), grace.id());

        System.out.println("all tasks:");
        List<Task> all = tasks.list();
        for (Task task : all) {
            System.out.println("  " + task.id() + " \"" + task.title()
                    + "\" -> assignee " + task.assigneeId());
        }
    }
}
