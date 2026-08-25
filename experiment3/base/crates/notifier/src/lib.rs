//! Notification domain: deliver messages, each tagged with a reference code.
//!
//! Depends on `corelib` only. Domain crates never depend on each other.

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

    /// Queue a notification. `at` is a unix timestamp in seconds.
    pub fn send(&mut self, recipient: &str, body: &str, at: i64) -> Notification {
        self.seq += 1;
        let n = Notification {
            reference: short_code(self.seq),
            recipient: recipient.to_string(),
            body: body.to_string(),
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
    fn sends_with_reference_and_time() {
        let mut n = Notifier::new();
        let sent = n.send("u1", "hello", 86_400);
        assert_eq!(sent.recipient, "u1");
        assert_eq!(sent.sent_at, "d1t0");
        assert_eq!(n.sent().len(), 1);
    }
}
