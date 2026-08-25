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
