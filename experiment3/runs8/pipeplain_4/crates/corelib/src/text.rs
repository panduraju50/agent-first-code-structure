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
    out.push('\u{2026}');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn truncates_with_ellipsis() {
        assert_eq!(truncate("abcdef", 4), "abc\u{2026}");
        assert_eq!(truncate("abc", 5), "abc");
    }
}
