/**
 * taskly.app — the composition root.
 *
 * This is the ONLY module allowed to require every other module: it is
 * where the domain graph gets wired together. tools/BoundaryCheck exempts
 * exactly this module from the "no broad imports" rule.
 */
module taskly.app {
    requires taskly.core;
    requires taskly.users;
    requires taskly.tasks;
}
