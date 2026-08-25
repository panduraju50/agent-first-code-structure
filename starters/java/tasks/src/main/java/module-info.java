/**
 * taskly.tasks — a domain module.
 *
 * Depends on taskly.core for id encoding + title validation. Does NOT
 * (and must not) require taskly.users — a task references an assignee only
 * as an opaque String id, never as a taskly.users.User. Adding
 * "requires taskly.users;" here is exactly the violation
 * tools/BoundaryCheck is built to catch.
 */
module taskly.tasks {
    requires taskly.core;

    exports taskly.tasks;
}
