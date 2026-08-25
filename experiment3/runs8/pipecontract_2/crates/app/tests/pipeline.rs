//! End-to-end checks over the notification pipeline.
//!
//! These span crates on purpose: they assert properties of a body as it travels
//! from the notifier through to the delivery endpoint, which no single crate's
//! unit tests can see.

use notifier::Notifier;

/// Bodies the product is expected to handle.
fn representative_bodies() -> Vec<String> {
    vec![
        "assigned to you".to_string(),
        "re: your ticket".to_string(),
        "status: open".to_string(),
        "a:b:c:d:e:f:g:h".to_string(),
        "pipe | separated".to_string(),
        "multi\nline".to_string(),
    ]
}

#[test]
fn every_body_the_notifier_accepts_can_be_delivered() {
    let mut n = Notifier::new();
    for body in representative_bodies() {
        let sent = n.send("u1", &body, 0);
        assert!(
            webhooks::accepts(&sent.body),
            "notifier produced a body the delivery endpoint rejects: \
             {:?} became {:?} ({} bytes)",
            body,
            sent.body,
            sent.body.len()
        );
    }
}

#[test]
fn a_delivered_body_still_reads_back_as_what_was_sent() {
    let mut n = Notifier::new();
    for body in representative_bodies() {
        let sent = n.send("u1", &body, 0);
        assert_eq!(search::unescape_body(&sent.body), body);
    }
}
