// unit: users (domains)
// capabilities: create_user, get_user
// effects: store
// uses: ids, validation
// GENERATED SKELETON — edges are declared in the project spec.

module taskly.users {
    requires taskly.ids;
    requires taskly.validation;
    exports taskly.users;
}
