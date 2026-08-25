//! Escaping for notification bodies.

/// Escape the characters that are significant in a notification body.
/// Backslash first, then the delimiters.
pub fn escape_body(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '|' => out.push_str("\\|"),
            '\n' => out.push_str("\\n"),
            ':' => out.push_str("\\:"),
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
        assert_eq!(escape_body("a|b"), "a\\|b");
        assert_eq!(escape_body("a\nb"), "a\\nb");
    }

    #[test]
    fn escapes_colon() {
        assert_eq!(escape_body("a:b"), "a\\:b");
        assert_eq!(escape_body("10:30"), "10\\:30");
    }
}
