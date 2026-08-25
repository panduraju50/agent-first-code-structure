// unit: tasks (domains)
// capabilities: create_task, list_tasks
// effects: store
// uses: ids, validation
// GENERATED SKELETON — edges are declared in the project spec.

module taskly.tasks {
    requires taskly.ids;
    requires taskly.validation;
    exports taskly.tasks;
}
