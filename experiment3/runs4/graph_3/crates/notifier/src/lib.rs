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
