package taskly.users;

/** A user record. Deliberately has no reference to anything in taskly.tasks. */
public record User(String id, String name, String email) {
}
