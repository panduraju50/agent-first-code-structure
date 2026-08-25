package taskly.tasks;

/**
 * A task record. {@code assigneeId} is an opaque String — this module has no
 * type-level knowledge of taskly.users.User, which is what keeps this edge
 * one-directional (tasks -> core only, never tasks -> users).
 */
public record Task(String id, String title, String assigneeId) {

    Task withAssignee(String newAssigneeId) {
        return new Task(id, title, newAssigneeId);
    }
}
