//! Hidden acceptance tests for the due-date feature.
//!
//! Copied into `crates/tasks/tests/` only AFTER an agent has finished, and
//! never shown to it. Scored automatically.
//!
//! Note on `renders_due_in_the_products_standard_format`: the task description
//! says the display format is "the product's standard timestamp display
//! format" and deliberately does not state what that is. Passing therefore
//! requires finding and reusing `corelib::timefmt::format_ts`. An agent that
//! re-implements formatting will produce a different string and fail — which
//! is exactly the cost of duplication, measured behaviourally.

use tasks::TaskStore;

const DAY: i64 = 86_400;

fn store_with(titles: &[&str]) -> (TaskStore, Vec<String>) {
    let mut s = TaskStore::new();
    let ids = titles.iter().map(|t| s.create(t).unwrap().id).collect();
    (s, ids)
}

#[test]
fn sets_and_reads_a_due_date() {
    let (mut s, ids) = store_with(&["write docs"]);
    s.set_due(&ids[0], 5 * DAY).unwrap();
    assert_eq!(s.get(&ids[0]).unwrap().due, Some(5 * DAY));
}

#[test]
fn due_defaults_to_none() {
    let (s, ids) = store_with(&["write docs"]);
    assert_eq!(s.get(&ids[0]).unwrap().due, None);
}

#[test]
fn rejects_unknown_task() {
    let (mut s, _) = store_with(&["write docs"]);
    assert!(s.set_due("nope", DAY).is_err());
}

#[test]
fn rejects_negative_due_date() {
    let (mut s, ids) = store_with(&["write docs"]);
    assert!(s.set_due(&ids[0], -1).is_err());
}

#[test]
fn clears_a_due_date() {
    let (mut s, ids) = store_with(&["write docs"]);
    s.set_due(&ids[0], 3 * DAY).unwrap();
    s.clear_due(&ids[0]).unwrap();
    assert_eq!(s.get(&ids[0]).unwrap().due, None);
}

#[test]
fn due_within_selects_the_window_inclusively() {
    let (mut s, ids) = store_with(&["a", "b", "c"]);
    s.set_due(&ids[0], 10 * DAY).unwrap(); // inside
    s.set_due(&ids[1], 12 * DAY).unwrap(); // exactly on the edge
    s.set_due(&ids[2], 20 * DAY).unwrap(); // outside
    let found: Vec<&str> = s
        .due_within(10 * DAY, 2 * DAY)
        .iter()
        .map(|t| t.title.as_str())
        .collect();
    assert_eq!(found, vec!["a", "b"]);
}

#[test]
fn due_within_excludes_undated_and_completed_tasks() {
    let (mut s, ids) = store_with(&["dated", "undated", "done"]);
    s.set_due(&ids[0], DAY).unwrap();
    s.set_due(&ids[2], DAY).unwrap();
    s.complete(&ids[2]).unwrap();
    let found: Vec<&str> = s
        .due_within(0, 2 * DAY)
        .iter()
        .map(|t| t.title.as_str())
        .collect();
    assert_eq!(found, vec!["dated"]);
}

#[test]
fn due_within_sorts_by_due_date_ascending() {
    let (mut s, ids) = store_with(&["later", "sooner"]);
    s.set_due(&ids[0], 5 * DAY).unwrap();
    s.set_due(&ids[1], 2 * DAY).unwrap();
    let found: Vec<&str> = s
        .due_within(0, 10 * DAY)
        .iter()
        .map(|t| t.title.as_str())
        .collect();
    assert_eq!(found, vec!["sooner", "later"]);
}

#[test]
fn due_within_excludes_dates_already_past() {
    let (mut s, ids) = store_with(&["overdue"]);
    s.set_due(&ids[0], DAY).unwrap();
    assert!(s.due_within(5 * DAY, DAY).is_empty());
}

#[test]
fn renders_due_in_the_products_standard_format() {
    let (mut s, ids) = store_with(&["write docs"]);
    s.set_due(&ids[0], 3 * DAY + 5).unwrap();
    assert_eq!(
        s.get(&ids[0]).unwrap().due_display(),
        Some("d3t5".to_string())
    );
}

#[test]
fn renders_no_display_without_a_due_date() {
    let (s, ids) = store_with(&["write docs"]);
    assert_eq!(s.get(&ids[0]).unwrap().due_display(), None);
}
