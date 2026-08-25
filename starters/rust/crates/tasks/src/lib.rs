//! `tasks` -- a domain module (Design D, rule 2).
//!
//! Depends on `corelib` only (see `Cargo.toml`). Must never depend on the
//! `users` domain: a `Task` references its assignee by an opaque
//! `String` id, not by importing `users::User`. That is what keeps this
//! crate's `Cargo.toml` free of a `users = { path = ... }` line, which is
//! exactly the edge boundary-lint checks for.

use corelib::new_id;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Task {
    pub id: String,
    pub title: String,
    pub assignee_id: Option<String>,
}

#[derive(Debug, Default)]
pub struct TaskStore {
    tasks: Vec<Task>,
    next_seed: u64,
}

impl TaskStore {
    pub fn new() -> Self {
        Self {
            tasks: Vec::new(),
            next_seed: 1,
        }
    }

    /// capability: task-creation
    ///
    /// Validates `title` via `corelib::validate::validate_title` and mints
    /// the id via `corelib::new_id`.
    pub fn create(&mut self, title: &str) -> Result<Task, String> {
        validate_title(title)?;

        let id = new_id(self.next_seed);
        self.next_seed += 1;

        let task = Task {
            id,
            title: title.to_string(),
            assignee_id: None,
        };
        self.tasks.push(task.clone());
        Ok(task)
    }

    /// capability: task-listing
    pub fn list(&self) -> &[Task] {
        &self.tasks
    }

    /// capability: task-assignment
    ///
    /// Takes `user_id` as a plain `&str` -- tasks does not know about (and
    /// must not import) the `users` crate's `User` type.
    pub fn assign(&mut self, task_id: &str, user_id: &str) -> Result<(), String> {
        let task = self
            .tasks
            .iter_mut()
            .find(|t| t.id == task_id)
            .ok_or_else(|| format!("no task with id {task_id}"))?;
        task.assignee_id = Some(user_id.to_string());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_list_and_assign() {
        let mut store = TaskStore::new();
        let task = store.create("Buy milk").unwrap();
        assert_eq!(store.list().len(), 1);

        store.assign(&task.id, "opaque-user-id-123").unwrap();
        assert_eq!(
            store.list()[0].assignee_id.as_deref(),
            Some("opaque-user-id-123")
        );
    }

    #[test]
    fn rejects_empty_title_via_core_validator() {
        let mut store = TaskStore::new();
        assert!(store.create("   ").is_err());
    }

    #[test]
    fn assign_unknown_task_is_an_error() {
        let mut store = TaskStore::new();
        assert!(store.assign("missing", "someone").is_err());
    }
}
