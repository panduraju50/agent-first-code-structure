//! Search over stored notification bodies.

use corelib::paging::page_slice;

pub fn matches(haystack: &str, needle: &str) -> bool {
    haystack.to_lowercase().contains(&needle.to_lowercase())
}

pub fn page<'a, T>(items: &'a [T], page_no: usize, size: usize) -> &'a [T] {
    page_slice(items, page_no, size)
}

/// Recover the original text from a stored notification body so it can be
/// matched against a plain search term.
pub fn unescape_body(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut chars = s.chars();
    while let Some(c) = chars.next() {
        if c != '\\' {
            out.push(c);
            continue;
        }
        match chars.next() {
            Some('n') => out.push('\n'),
            Some('|') => out.push('|'),
            Some('\\') => out.push('\\'),
            Some(other) => {
                out.push('\\');
                out.push(other);
            }
            None => out.push('\\'),
        }
    }
    out
}

/// Search a stored (escaped) body for a plain-text term.
pub fn search_body(stored: &str, term: &str) -> bool {
    matches(&unescape_body(stored), term)
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

    #[test]
    fn round_trips_a_stored_body() {
        assert_eq!(unescape_body("a\\|b"), "a|b");
        assert!(search_body("a\\|b", "a|b"));
    }
}
