#!/usr/bin/env python3
"""Build the v2 experiment base: a Rust workspace large enough that reading it
exhaustively is not a viable strategy.

What changed from v1, and why:

  no signposts     v1's `timefmt.rs` opened with a doc comment saying every
                   user-visible timestamp goes through `format_ts`. Agents
                   quoted it back. That is an answer key planted in the
                   artifact, so every doc comment advertising a primitive as
                   canonical is gone.

  scale            v1 was 383 lines over 8 files and was solved after reading
                   3-5 of them. Context and retrieval cannot matter at that
                   size. v2 is ~15 crates.

  decoys           a `legacy` crate holds plausible near-misses: functions with
                   the obvious names that COMPILE and look right but behave
                   differently. Grep alone now picks the wrong one.

  many traps       the feature needs seven separate primitives, so the score is
                   a gradient rather than one coin flip.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "base_v2"

# --------------------------------------------------------------------------
# corelib — the real primitives. Deliberately unremarkable module docs.
# --------------------------------------------------------------------------

CORE = {
"lib.rs": """
pub mod escape;
pub mod ids;
pub mod paging;
pub mod priority;
pub mod text;
pub mod timefmt;
pub mod validate;
""",

"ids.rs": '''
//! Reference code helpers.

const ALPHABET: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

pub fn short_code(mut n: u64) -> String {
    if n == 0 {
        return "0".to_string();
    }
    let mut out = Vec::new();
    while n > 0 {
        out.push(ALPHABET[(n % 62) as usize]);
        n /= 62;
    }
    out.reverse();
    String::from_utf8(out).expect("ascii")
}

pub fn decode_code(s: &str) -> Option<u64> {
    let mut n: u64 = 0;
    for b in s.bytes() {
        let idx = ALPHABET.iter().position(|&c| c == b)?;
        n = n.checked_mul(62)?.checked_add(idx as u64)?;
    }
    Some(n)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        for n in [0u64, 1, 61, 62, 4000] {
            assert_eq!(decode_code(&short_code(n)), Some(n));
        }
    }
}
''',

"timefmt.rs": '''
//! Timestamp helpers.

pub const SECONDS_PER_DAY: i64 = 86_400;

pub fn format_ts(ts: i64) -> String {
    let day = ts.div_euclid(SECONDS_PER_DAY);
    let rem = ts.rem_euclid(SECONDS_PER_DAY);
    format!("d{}t{}", day, rem)
}

pub fn parse_ts(s: &str) -> Option<i64> {
    let rest = s.strip_prefix('d')?;
    let (day, secs) = rest.split_once('t')?;
    let day: i64 = day.parse().ok()?;
    let secs: i64 = secs.parse().ok()?;
    if !(0..SECONDS_PER_DAY).contains(&secs) {
        return None;
    }
    Some(day * SECONDS_PER_DAY + secs)
}

pub fn days_between(from: i64, to: i64) -> i64 {
    (to - from).div_euclid(SECONDS_PER_DAY)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        for ts in [0i64, 1, 86_399, 86_400] {
            assert_eq!(parse_ts(&format_ts(ts)), Some(ts));
        }
    }
}
''',

"text.rs": '''
//! Text shaping helpers.

/// Shorten `s` to at most `max` characters, marking truncation with a single
/// Unicode ellipsis that counts toward the limit.
pub fn truncate(s: &str, max: usize) -> String {
    if max == 0 {
        return String::new();
    }
    let count = s.chars().count();
    if count <= max {
        return s.to_string();
    }
    let keep = max - 1;
    let mut out: String = s.chars().take(keep).collect();
    out.push('\\u{2026}');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn truncates_with_ellipsis() {
        assert_eq!(truncate("abcdef", 4), "abc\\u{2026}");
        assert_eq!(truncate("abc", 5), "abc");
    }
}
''',

"paging.rs": '''
//! Slicing a list into pages. Pages are 1-indexed.

pub fn page_slice<T>(items: &[T], page: usize, size: usize) -> &[T] {
    if size == 0 || page == 0 {
        return &[];
    }
    let start = (page - 1) * size;
    if start >= items.len() {
        return &[];
    }
    let end = usize::min(start + size, items.len());
    &items[start..end]
}

pub fn page_count(total: usize, size: usize) -> usize {
    if size == 0 {
        return 0;
    }
    total.div_ceil(size)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn first_page_is_page_one() {
        let v = [1, 2, 3, 4, 5];
        assert_eq!(page_slice(&v, 1, 2), &[1, 2]);
        assert_eq!(page_slice(&v, 3, 2), &[5]);
    }
}
''',

"priority.rs": '''
//! Priority levels.

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum Priority {
    Low,
    Normal,
    High,
    Urgent,
}

/// Render a priority as the short tag used in user-facing summaries.
pub fn priority_label(p: Priority) -> &'static str {
    match p {
        Priority::Low => "[-]",
        Priority::Normal => "[ ]",
        Priority::High => "[!]",
        Priority::Urgent => "[!!]",
    }
}

pub fn parse_priority(s: &str) -> Option<Priority> {
    match s.trim().to_ascii_lowercase().as_str() {
        "low" => Some(Priority::Low),
        "normal" => Some(Priority::Normal),
        "high" => Some(Priority::High),
        "urgent" => Some(Priority::Urgent),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn labels() {
        assert_eq!(priority_label(Priority::High), "[!]");
        assert_eq!(parse_priority("Urgent"), Some(Priority::Urgent));
    }
}
''',

"escape.rs": '''
//! Escaping for notification bodies.

/// Escape the characters that are significant in a notification body.
/// Backslash first, then the delimiters.
pub fn escape_body(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '\\\\' => out.push_str("\\\\\\\\"),
            '|' => out.push_str("\\\\|"),
            '\\n' => out.push_str("\\\\n"),
            _ => out.push(c),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn escapes_pipe_and_newline() {
        assert_eq!(escape_body("a|b"), "a\\\\|b");
        assert_eq!(escape_body("a\\nb"), "a\\\\nb");
    }
}
''',

"validate.rs": '''
//! Input validation.

pub fn validate_title(title: &str) -> Result<(), String> {
    let t = title.trim();
    if t.is_empty() {
        return Err("title must not be blank".into());
    }
    if t.chars().count() > 200 {
        return Err("title must be at most 200 characters".into());
    }
    Ok(())
}

pub fn validate_email(email: &str) -> Result<(), String> {
    let e = email.trim();
    let (local, domain) = e.split_once('@').ok_or("email must contain '@'")?;
    if local.is_empty() {
        return Err("email must have a local part".into());
    }
    if !domain.contains('.') || domain.starts_with('.') || domain.ends_with('.') {
        return Err("email must have a valid domain".into());
    }
    Ok(())
}

/// Check that `value` falls within `lo..=hi`, naming the field in the error.
pub fn validate_range(field: &str, value: i64, lo: i64, hi: i64) -> Result<(), String> {
    if value < lo || value > hi {
        return Err(format!("{field} must be between {lo} and {hi}"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ranges() {
        assert!(validate_range("window", 5, 0, 10).is_ok());
        assert_eq!(
            validate_range("window", 11, 0, 10).unwrap_err(),
            "window must be between 0 and 10"
        );
    }
}
''',
}

# --------------------------------------------------------------------------
# legacy — decoys. These compile, read plausibly, and are WRONG for the task.
# Their names are the ones an agent reaches for first.
# --------------------------------------------------------------------------

LEGACY = {
"lib.rs": """
pub mod checks;
pub mod display;
pub mod listing;
pub mod strings;
pub mod tokens;
""",

"display.rs": '''
//! Older presentation helpers retained for the v1 export path.

/// Human-ish rendering used by the v1 CSV export.
pub fn render_time(ts: i64) -> String {
    let days = ts / 86_400;
    let hours = (ts % 86_400) / 3_600;
    format!("{days} days {hours}h")
}

pub fn render_flag(on: bool) -> &'static str {
    if on {
        "yes"
    } else {
        "no"
    }
}
''',

"tokens.rs": '''
//! Token helpers for the v1 export path.

const CHARS: &[u8] = b"abcdefghijkmnpqrstuvwxyz23456789";

/// Base32-ish token, ambiguous characters removed.
pub fn make_token(mut n: u64) -> String {
    if n == 0 {
        return "a".to_string();
    }
    let mut out = Vec::new();
    while n > 0 {
        out.push(CHARS[(n % 32) as usize]);
        n /= 32;
    }
    out.reverse();
    String::from_utf8(out).expect("ascii")
}
''',

"strings.rs": '''
//! Older string helpers.

/// Clip to `max` characters and append three dots.
pub fn shorten(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        return s.to_string();
    }
    let mut out: String = s.chars().take(max).collect();
    out.push_str("...");
    out
}
''',

"listing.rs": '''
//! Older listing helpers. Pages here are 0-indexed.

pub fn take_page<T>(items: &[T], page: usize, size: usize) -> &[T] {
    if size == 0 {
        return &[];
    }
    let start = page * size;
    if start >= items.len() {
        return &[];
    }
    &items[start..usize::min(start + size, items.len())]
}
''',

"checks.rs": '''
//! Older bounds checks. Exclusive upper bound.

pub fn in_bounds(value: i64, lo: i64, hi: i64) -> bool {
    value >= lo && value < hi
}
''',
}

# --------------------------------------------------------------------------
# Domain bulk. Real CRUD so the repo has genuine mass to search through.
# --------------------------------------------------------------------------

def domain_crate(name: str, entity: str, fields: list[tuple[str, str]], validated: str | None) -> str:
    struct_fields = "\n".join(f"    pub {f}: {t}," for f, t in fields)
    init = "\n".join(
        f"            {f}: {f}.trim().to_string()," if t == "String" else f"            {f}: {f},"
        for f, t in fields
        if f != "id"
    )
    args = ", ".join(
        f"{f}: &str" if t == "String" else f"{f}: {t}" for f, t in fields if f != "id"
    )
    validate_line = (
        f"        validate_{validated}({fields[1][0]})?;\n" if validated else ""
    )
    use_validate = (
        f"use corelib::validate::validate_{validated};\n" if validated else ""
    )
    return f'''
use corelib::ids::short_code;
{use_validate}
#[derive(Debug, Clone, PartialEq)]
pub struct {entity} {{
{struct_fields}
}}

#[derive(Default)]
pub struct {entity}Store {{
    items: Vec<{entity}>,
    seq: u64,
}}

impl {entity}Store {{
    pub fn new() -> Self {{
        Self::default()
    }}

    pub fn create(&mut self, {args}) -> Result<{entity}, String> {{
{validate_line}        self.seq += 1;
        let item = {entity} {{
            id: short_code(self.seq),
{init}
        }};
        self.items.push(item.clone());
        Ok(item)
    }}

    pub fn get(&self, id: &str) -> Option<&{entity}> {{
        self.items.iter().find(|i| i.id == id)
    }}

    pub fn list(&self) -> &[{entity}] {{
        &self.items
    }}

    pub fn remove(&mut self, id: &str) -> Result<(), String> {{
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {{
            return Err(format!("no such {name}: {{id}}"));
        }}
        Ok(())
    }}

    pub fn count(&self) -> usize {{
        self.items.len()
    }}
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn creates_and_reads() {{
        let mut s = {entity}Store::new();
        let item = s.create({{sample}}).unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }}

    #[test]
    fn removes() {{
        let mut s = {entity}Store::new();
        let item = s.create({{sample}}).unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }}
}}
'''.replace(
        "{sample}",
        ", ".join(
            '"x@y.com"' if (validated == "email" and i == 1)
            else '"sample"' if t == "String"
            else "0"
            for i, (f, t) in enumerate(fields)
            if f != "id"
        ),
    )


DOMAINS = [
    ("projects", "Project", [("id", "String"), ("name", "String"), ("owner", "String")], "title"),
    ("tags", "Tag", [("id", "String"), ("label", "String"), ("colour", "String")], "title"),
    ("comments", "Comment", [("id", "String"), ("body", "String"), ("author", "String")], "title"),
    ("labels", "Label", [("id", "String"), ("name", "String"), ("kind", "String")], "title"),
    ("attachments", "Attachment", [("id", "String"), ("filename", "String"), ("mime", "String")], "title"),
    ("audit", "AuditEntry", [("id", "String"), ("action", "String"), ("actor", "String")], "title"),
    ("teams", "Team", [("id", "String"), ("name", "String"), ("lead", "String")], "title"),
    ("webhooks", "Webhook", [("id", "String"), ("url", "String"), ("secret", "String")], "title"),
]

TASKS_CRATE = '''
use corelib::ids::short_code;
use corelib::priority::Priority;
use corelib::validate::validate_title;

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
'''

USERS_CRATE = '''
use corelib::ids::short_code;
use corelib::validate::validate_email;

#[derive(Debug, Clone, PartialEq)]
pub struct User {
    pub id: String,
    pub email: String,
}

#[derive(Default)]
pub struct UserStore {
    users: Vec<User>,
    seq: u64,
}

impl UserStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, email: &str) -> Result<User, String> {
        validate_email(email)?;
        if self.users.iter().any(|u| u.email == email.trim()) {
            return Err("email already registered".into());
        }
        self.seq += 1;
        let user = User {
            id: short_code(self.seq),
            email: email.trim().to_string(),
        };
        self.users.push(user.clone());
        Ok(user)
    }

    pub fn get(&self, id: &str) -> Option<&User> {
        self.users.iter().find(|u| u.id == id)
    }

    pub fn count(&self) -> usize {
        self.users.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_user() {
        let mut s = UserStore::new();
        let u = s.create("a@b.com").unwrap();
        assert_eq!(s.get(&u.id).unwrap().email, "a@b.com");
    }

    #[test]
    fn rejects_bad_and_duplicate() {
        let mut s = UserStore::new();
        assert!(s.create("nope").is_err());
        s.create("a@b.com").unwrap();
        assert!(s.create("a@b.com").is_err());
    }
}
'''

NOTIFIER_CRATE = '''
use corelib::escape::escape_body;
use corelib::ids::short_code;
use corelib::timefmt::format_ts;

#[derive(Debug, Clone, PartialEq)]
pub struct Notification {
    pub reference: String,
    pub recipient: String,
    pub body: String,
    pub sent_at: String,
}

#[derive(Default)]
pub struct Notifier {
    sent: Vec<Notification>,
    seq: u64,
}

impl Notifier {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn send(&mut self, recipient: &str, body: &str, at: i64) -> Notification {
        self.seq += 1;
        let n = Notification {
            reference: short_code(self.seq),
            recipient: recipient.to_string(),
            body: escape_body(body),
            sent_at: format_ts(at),
        };
        self.sent.push(n.clone());
        n
    }

    pub fn sent(&self) -> &[Notification] {
        &self.sent
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sends() {
        let mut n = Notifier::new();
        let s = n.send("u1", "hi", 86_400);
        assert_eq!(s.sent_at, "d1t0");
        assert_eq!(n.sent().len(), 1);
    }
}
'''

SEARCH_CRATE = '''
use corelib::paging::page_slice;

pub fn matches(haystack: &str, needle: &str) -> bool {
    haystack.to_lowercase().contains(&needle.to_lowercase())
}

pub fn page<'a, T>(items: &'a [T], page_no: usize, size: usize) -> &'a [T] {
    page_slice(items, page_no, size)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finds_and_pages() {
        assert!(matches("Write Docs", "docs"));
        let v = [1, 2, 3];
        assert_eq!(page(&v, 1, 2), &[1, 2]);
    }
}
'''

APP_CRATE = '''
use notifier::Notifier;
use tasks::TaskStore;
use users::UserStore;

fn main() {
    let mut users = UserStore::new();
    let mut tasks = TaskStore::new();
    let mut notifier = Notifier::new();

    let alice = users.create("alice@example.com").expect("valid email");
    let task = tasks.create("p1", "write the report").expect("valid title");
    tasks.assign(&task.id, &alice.id).expect("task exists");
    let note = notifier.send(&alice.id, &format!("assigned: {}", task.title), 0);

    println!("user {} task {} note {}", alice.id, task.id, note.reference);
}
'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def cargo_toml(name: str, deps: list[str]) -> str:
    body = "".join(f'{d} = {{ path = "../{d}" }}\n' for d in deps)
    return f'[package]\nname = "{name}"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\n{body}'


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)

    crates = ["corelib", "legacy", "users", "tasks", "notifier", "search", "app"]
    crates += [d[0] for d in DOMAINS]

    members = ", ".join(f'"crates/{c}"' for c in sorted(crates))
    write(OUT / "Cargo.toml", f'[workspace]\nresolver = "2"\nmembers = [{members}]\n')

    for fname, content in CORE.items():
        write(OUT / "crates/corelib/src" / fname, content)
    write(OUT / "crates/corelib/Cargo.toml", cargo_toml("corelib", []))

    for fname, content in LEGACY.items():
        write(OUT / "crates/legacy/src" / fname, content)
    write(OUT / "crates/legacy/Cargo.toml", cargo_toml("legacy", []))

    write(OUT / "crates/tasks/src/lib.rs", TASKS_CRATE)
    write(OUT / "crates/tasks/Cargo.toml", cargo_toml("tasks", ["corelib"]))
    write(OUT / "crates/users/src/lib.rs", USERS_CRATE)
    write(OUT / "crates/users/Cargo.toml", cargo_toml("users", ["corelib"]))
    write(OUT / "crates/notifier/src/lib.rs", NOTIFIER_CRATE)
    write(OUT / "crates/notifier/Cargo.toml", cargo_toml("notifier", ["corelib"]))
    write(OUT / "crates/search/src/lib.rs", SEARCH_CRATE)
    write(OUT / "crates/search/Cargo.toml", cargo_toml("search", ["corelib"]))

    for name, entity, fields, validated in DOMAINS:
        write(OUT / f"crates/{name}/src/lib.rs", domain_crate(name, entity, fields, validated))
        write(OUT / f"crates/{name}/Cargo.toml", cargo_toml(name, ["corelib"]))

    write(OUT / "crates/app/src/main.rs", APP_CRATE)
    write(OUT / "crates/app/Cargo.toml", cargo_toml("app", ["corelib", "users", "tasks", "notifier"]))

    files = list(OUT.rglob("*.rs"))
    lines = sum(len(p.read_text().splitlines()) for p in files)
    print(f"built {OUT.name}: {len(crates)} crates, {len(files)} rust files, {lines} lines")


if __name__ == "__main__":
    main()
