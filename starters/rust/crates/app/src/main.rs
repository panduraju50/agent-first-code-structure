//! `app` -- the composition root (Design D, rule 2).
//!
//! This is the only crate in the workspace allowed to import both `users`
//! and `tasks`. It wires the domains together and runs a tiny end-to-end
//! scenario. It contains no business rules of its own -- id encoding,
//! validation, user creation, and task creation all live in `corelib`,
//! `users`, and `tasks` respectively.

use tasks::TaskStore;
use users::UserStore;

fn main() {
    let mut user_store = UserStore::new();
    let mut task_store = TaskStore::new();

    let ada = user_store
        .create("Ada Lovelace", "ada@example.com")
        .expect("seed user is valid");
    println!("created user {} <{}> \"{}\"", ada.id, ada.email, ada.name);

    let write_program = task_store
        .create("Write the first published algorithm")
        .expect("seed task is valid");
    let review_notes = task_store
        .create("Review Babbage's engine notes")
        .expect("seed task is valid");

    task_store
        .assign(&write_program.id, &ada.id)
        .expect("task exists");

    println!("\ntasks:");
    for t in task_store.list() {
        println!(
            "  [{}] '{}' assigned_to={:?}",
            t.id, t.title, t.assignee_id
        );
    }

    // Look the user back up purely by the id string tasks stored --
    // demonstrating that tasks never needed to import `users::User` to
    // reference a user.
    if let Some(found) = user_store.get(&ada.id) {
        println!("\nlooked up assignee of '{}': {found:?}", write_program.title);
    }

    // review_notes exists but stays unassigned in this scenario.
    println!(
        "\n'{}' remains unassigned: {}",
        review_notes.title,
        task_store
            .list()
            .iter()
            .find(|t| t.id == review_notes.id)
            .unwrap()
            .assignee_id
            .is_none()
    );
}
