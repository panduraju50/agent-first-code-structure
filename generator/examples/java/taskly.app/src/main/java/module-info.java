// unit: app (app)
// capabilities: run
// effects: store, net
// uses: users, tasks, notifier
// GENERATED SKELETON — edges are declared in the project spec.

module taskly.app {
    requires taskly.users;
    requires taskly.tasks;
    requires taskly.notifier;
    exports taskly.app;
}
