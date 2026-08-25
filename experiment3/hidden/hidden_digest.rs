//! Hidden acceptance tests for the task-digest feature.
//!
//! Installed only AFTER an agent finishes; never shown to it.
//!
//! Each assertion below is a separate trap. The feature needs seven primitives
//! that already exist in `corelib`, and for each one the `legacy` crate offers a
//! plausible near-miss that compiles and reads correctly but behaves
//! differently. The task description never says which to use, so the score is a
//! gradient over how many were retrieved correctly rather than one coin flip.
//!
//!   time format     corelib::timefmt::format_ts   vs legacy::display::render_time
//!   reference code  corelib::ids::short_code      vs legacy::tokens::make_token
//!   truncation      corelib::text::truncate       vs legacy::strings::shorten
//!   paging          corelib::paging::page_slice   vs legacy::listing::take_page
//!   range check     corelib::validate::validate_range vs legacy::checks::in_bounds
//!   priority tag    corelib::priority::priority_label
//!   escaping        corelib::escape::escape_body

use corelib::priority::Priority;
use tasks::{build_digest, DigestOptions, TaskStore};

const DAY: i64 = 86_400;

fn opts(now: i64, window_days: i64) -> DigestOptions {
    DigestOptions {
        now,
        window_days,
        page: 1,
        page_size: 10,
        title_max: 20,
    }
}

fn store(titles: &[(&str, i64)]) -> TaskStore {
    let mut s = TaskStore::new();
    for (title, due) in titles {
        let t = s.create("p1", title).unwrap();
        s.set_due(&t.id, *due).unwrap();
    }
    s
}

#[test]
fn selects_only_tasks_inside_the_window() {
    let s = store(&[("inside", 2 * DAY), ("edge", 5 * DAY), ("outside", 9 * DAY)]);
    let d = build_digest(s.list(), 1, &opts(0, 5)).unwrap();
    assert_eq!(d.lines.len(), 2);
}

#[test]
fn excludes_completed_and_undated_tasks() {
    let mut s = store(&[("dated", DAY), ("done", DAY)]);
    let done_id = s.list()[1].id.clone();
    s.complete(&done_id).unwrap();
    s.create("p1", "undated").unwrap();
    let d = build_digest(s.list(), 1, &opts(0, 5)).unwrap();
    assert_eq!(d.lines.len(), 1);
}

#[test]
fn sorts_by_due_date_ascending() {
    let s = store(&[("later", 4 * DAY), ("sooner", 1 * DAY)]);
    let d = build_digest(s.list(), 1, &opts(0, 10)).unwrap();
    assert!(d.lines[0].contains("sooner"), "got {:?}", d.lines);
}

// TRAP 1: the timestamp rendering. legacy::display::render_time would produce
// "2 days 0h" instead of "d2t0".
#[test]
fn renders_the_due_date_in_the_products_timestamp_format() {
    let s = store(&[("write docs", 2 * DAY)]);
    let d = build_digest(s.list(), 1, &opts(0, 5)).unwrap();
    assert_eq!(d.lines[0], "[ ] write docs | due d2t0");
}

// TRAP 2: the reference code. legacy::tokens::make_token would give "bq".
#[test]
fn stamps_the_digest_with_a_reference_code() {
    let s = store(&[("a", DAY)]);
    assert_eq!(build_digest(s.list(), 62, &opts(0, 5)).unwrap().reference, "10");
    assert_eq!(build_digest(s.list(), 61, &opts(0, 5)).unwrap().reference, "Z");
}

// TRAP 3: truncation. legacy::strings::shorten appends "..." and does not count
// the marker toward the limit.
#[test]
fn truncates_long_titles_with_the_products_ellipsis() {
    let s = store(&[("abcdefghij", DAY)]);
    let mut o = opts(0, 5);
    o.title_max = 5;
    let d = build_digest(s.list(), 1, &o).unwrap();
    assert_eq!(d.lines[0], "[ ] abcd\u{2026} | due d1t0");
}

// TRAP 4: paging is 1-indexed. legacy::listing::take_page is 0-indexed, so it
// would return the second page here.
#[test]
fn page_one_is_the_first_page() {
    let s = store(&[("first", DAY), ("second", 2 * DAY)]);
    let mut o = opts(0, 5);
    o.page_size = 1;
    let d = build_digest(s.list(), 1, &o).unwrap();
    assert_eq!(d.lines.len(), 1);
    assert!(d.lines[0].contains("first"), "got {:?}", d.lines);
}

#[test]
fn reports_the_total_page_count() {
    let s = store(&[("a", DAY), ("b", 2 * DAY), ("c", 3 * DAY)]);
    let mut o = opts(0, 5);
    o.page_size = 2;
    assert_eq!(build_digest(s.list(), 1, &o).unwrap().total_pages, 2);
}

// TRAP 5: the range check is inclusive on both ends and carries a specific
// message. legacy::checks::in_bounds is exclusive at the top.
#[test]
fn accepts_the_inclusive_window_bounds() {
    let s = store(&[("a", DAY)]);
    assert!(build_digest(s.list(), 1, &opts(0, 1)).is_ok());
    assert!(build_digest(s.list(), 1, &opts(0, 30)).is_ok());
}

#[test]
fn rejects_a_window_outside_the_allowed_range() {
    let s = store(&[("a", DAY)]);
    match build_digest(s.list(), 1, &opts(0, 31)) {
        Err(e) => assert_eq!(e, "window_days must be between 1 and 30"),
        Ok(_) => panic!("a 31-day window must be rejected"),
    }
    assert!(build_digest(s.list(), 1, &opts(0, 0)).is_err());
}

// TRAP 6: the priority tag.
#[test]
fn tags_each_line_with_the_priority_label() {
    let mut s = store(&[("urgent thing", DAY)]);
    let id = s.list()[0].id.clone();
    s.set_priority(&id, Priority::Urgent).unwrap();
    let d = build_digest(s.list(), 1, &opts(0, 5)).unwrap();
    assert_eq!(d.lines[0], "[!!] urgent thing | due d1t0");
}

// TRAP 7: escaping. An unescaped pipe would corrupt the delimiter.
#[test]
fn escapes_delimiters_in_the_title() {
    let s = store(&[("a|b", DAY)]);
    let d = build_digest(s.list(), 1, &opts(0, 5)).unwrap();
    assert_eq!(d.lines[0], "[ ] a\\|b | due d1t0");
}
