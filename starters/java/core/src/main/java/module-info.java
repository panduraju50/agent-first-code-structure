/**
 * taskly.core — the ONLY module allowed to define cross-cutting primitives.
 *
 * This is the typed-dependency-graph root: it depends on nothing of ours,
 * and exports exactly the two packages that hold the primitives every
 * domain module is required to reuse instead of reimplementing.
 */
module taskly.core {
    exports taskly.core.id;
    exports taskly.core.validate;
}
