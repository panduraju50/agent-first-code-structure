/**
 * taskly.users — a domain module.
 *
 * Depends on taskly.core for id encoding + email/name validation. Does NOT
 * (and must not) require taskly.tasks — the compiler enforces this: nothing
 * in this module can import taskly.tasks.* because it is not on the require
 * list, and tools/BoundaryCheck fails the build if that line is ever added.
 */
module taskly.users {
    requires taskly.core;

    exports taskly.users;
}
