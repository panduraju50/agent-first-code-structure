use corelib::escape::escape_body;
use corelib::ids::short_code;
use corelib::paging::{page_count, page_slice};
use corelib::priority::{priority_label, Priority};
use corelib::text::truncate;
use corelib::timefmt::{format_ts, SECONDS_PER_DAY};
use corelib::validate::{validate_range, validate_title};

#[derive(Debug, Clone, PartialEq)]
pub struct Task {
    pub id: String,
    pub project: String,
    pub title: String,
    pub done: bool,
    pub assignee: Option<String>,
    pub priority: Priority,
    pub due: Option<i64>,
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

    pub fn create(&mut self, project: &str, title: &str) -> Result<Task, String> {
        validate_title(title)?;
        self.seq += 1;
        let task = Task {
            id: short_code(self.seq),
            project: project.trim().to_string(),
            title: title.trim().to_string(),
            done: false,
            assignee: None,
            priority: Priority::Normal,
            due: None,
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

    pub fn in_project(&self, project: &str) -> Vec<&Task> {
        self.tasks.iter().filter(|t| t.project == project).collect()
    }

    pub fn complete(&mut self, id: &str) -> Result<(), String> {
        let t = self.find_mut(id)?;
        t.done = true;
        Ok(())
    }

    pub fn assign(&mut self, id: &str, user_id: &str) -> Result<(), String> {
        let t = self.find_mut(id)?;
        t.assignee = Some(user_id.to_string());
        Ok(())
    }

    pub fn set_priority(&mut self, id: &str, p: Priority) -> Result<(), String> {
        let t = self.find_mut(id)?;
        t.priority = p;
        Ok(())
    }

    pub fn set_due(&mut self, id: &str, due_ts: i64) -> Result<(), String> {
        let t = self.find_mut(id)?;
        t.due = Some(due_ts);
        Ok(())
    }

    fn find_mut(&mut self, id: &str) -> Result<&mut Task, String> {
        self.tasks
            .iter_mut()
            .find(|t| t.id == id)
            .ok_or_else(|| format!("no such task: {id}"))
    }
}

/// Options controlling how a task digest is assembled.
pub struct DigestOptions {
    pub now: i64,
    pub window_days: i64,
    pub page: usize,
    pub page_size: usize,
    pub title_max: usize,
}

/// A page of a task digest.
pub struct Digest {
    pub reference: String,
    pub lines: Vec<String>,
    pub total_pages: usize,
}

/// Build one page of a digest of upcoming, not-done tasks.
///
/// Selects tasks that are not done and whose due date falls within
/// `[now, now + window_days]` (inclusive), sorted by due date ascending,
/// then returns the requested page rendered as summary lines.
pub fn build_digest(tasks: &[Task], seq: u64, opts: &DigestOptions) -> Result<Digest, String> {
    validate_range("window_days", opts.window_days, 1, 30)?;

    let window_end = opts.now + opts.window_days * SECONDS_PER_DAY;

    let mut selected: Vec<&Task> = tasks
        .iter()
        .filter(|t| !t.done)
        .filter(|t| matches!(t.due, Some(d) if d >= opts.now && d <= window_end))
        .collect();
    selected.sort_by_key(|t| t.due.expect("filtered to tasks with a due date"));

    let total_pages = page_count(selected.len(), opts.page_size);
    let page_items = page_slice(&selected, opts.page, opts.page_size);

    let lines = page_items
        .iter()
        .map(|t| {
            let shortened = truncate(&t.title, opts.title_max);
            let safe_title = escape_body(&shortened);
            let due = t.due.expect("filtered to tasks with a due date");
            format!(
                "{} {} | due {}",
                priority_label(t.priority),
                safe_title,
                format_ts(due)
            )
        })
        .collect();

    Ok(Digest {
        reference: short_code(seq),
        lines,
        total_pages,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_and_lists() {
        let mut s = TaskStore::new();
        let t = s.create("p1", "write docs").unwrap();
        assert_eq!(s.get(&t.id).unwrap().title, "write docs");
        assert_eq!(s.in_project("p1").len(), 1);
    }

    #[test]
    fn rejects_blank_title() {
        let mut s = TaskStore::new();
        assert!(s.create("p1", "  ").is_err());
    }

    #[test]
    fn completes_assigns_prioritises() {
        let mut s = TaskStore::new();
        let t = s.create("p1", "ship").unwrap();
        s.complete(&t.id).unwrap();
        s.assign(&t.id, "u1").unwrap();
        s.set_priority(&t.id, Priority::High).unwrap();
        s.set_due(&t.id, 86_400).unwrap();
        let got = s.get(&t.id).unwrap();
        assert!(got.done);
        assert_eq!(got.priority, Priority::High);
        assert_eq!(got.due, Some(86_400));
    }
}
