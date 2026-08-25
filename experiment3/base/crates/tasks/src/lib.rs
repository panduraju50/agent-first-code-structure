//! Task domain: create, list, complete and assign tasks.
//!
//! Depends on `corelib` only. Domain crates never depend on each other.

use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Task {
    pub id: String,
    pub title: String,
    pub done: bool,
    pub assignee: Option<String>,
}

#[derive(Default)]
pub struct TaskStore {
    tasks: Vec<Task>,
    seq: u64,
}

impl TaskStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, title: &str) -> Result<Task, String> {
        validate_title(title)?;
        self.seq += 1;
        let task = Task {
            id: short_code(self.seq),
            title: title.trim().to_string(),
            done: false,
            assignee: None,
        };
        self.tasks.push(task.clone());
        Ok(task)
    }

    pub fn get(&self, id: &str) -> Option<&Task> {
        self.tasks.iter().find(|t| t.id == id)
    }

    pub fn list(&self) -> &[Task] {
        &self.tasks
    }

    pub fn complete(&mut self, id: &str) -> Result<(), String> {
        let task = self
            .tasks
            .iter_mut()
            .find(|t| t.id == id)
            .ok_or_else(|| format!("no such task: {id}"))?;
        task.done = true;
        Ok(())
    }

    pub fn assign(&mut self, id: &str, user_id: &str) -> Result<(), String> {
        let task = self
            .tasks
            .iter_mut()
            .find(|t| t.id == id)
            .ok_or_else(|| format!("no such task: {id}"))?;
        task.assignee = Some(user_id.to_string());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_and_lists() {
        let mut s = TaskStore::new();
        let t = s.create("write docs").unwrap();
        assert_eq!(s.list().len(), 1);
        assert_eq!(s.get(&t.id).unwrap().title, "write docs");
    }

    #[test]
    fn rejects_blank_title() {
        let mut s = TaskStore::new();
        assert!(s.create("  ").is_err());
    }

    #[test]
    fn completes_and_assigns() {
        let mut s = TaskStore::new();
        let t = s.create("ship it").unwrap();
        s.complete(&t.id).unwrap();
        s.assign(&t.id, "u1").unwrap();
        let got = s.get(&t.id).unwrap();
        assert!(got.done);
        assert_eq!(got.assignee.as_deref(), Some("u1"));
    }
}
