//! Hidden acceptance tests for the escaping change.
//!
//! Installed only AFTER an agent finishes; never shown to it.
//!
//! The change itself is one line in `corelib::escape::escape_body`. What is
//! being measured is whether the agent finds the two INDIRECT dependents:
//!
//!   search::unescape_body   the inverse. Never calls escape_body, but must
//!                           agree with it or a stored body no longer round-trips.
//!   webhooks::split_headers assumes an unescaped ':' is a delimiter, so it must
//!                           stop splitting on one that is now escaped.
//!
//! Neither is reachable by grepping for `escape_body`, and the compiler is
//! silent about both: this is a semantic change, not a signature change.

use corelib::escape::escape_body;

#[test]
fn escapes_the_new_delimiter() {
    assert_eq!(escape_body("to:alice"), "to\\:alice");
}

#[test]
fn still_escapes_the_existing_delimiters() {
    assert_eq!(escape_body("a|b"), "a\\|b");
    assert_eq!(escape_body("a\nb"), "a\\nb");
    assert_eq!(escape_body("a\\b"), "a\\\\b");
}

#[test]
fn leaves_ordinary_text_alone() {
    assert_eq!(escape_body("hello world"), "hello world");
}

// DEPENDENT 1: the inverse must track the change, or a stored body stops
// round-tripping. `search` never calls `escape_body`.
#[test]
fn the_inverse_recovers_the_new_escape() {
    assert_eq!(search::unescape_body("to\\:alice"), "to:alice");
}

#[test]
fn a_body_survives_a_full_round_trip() {
    for original in ["to:alice", "a|b", "plain", "mixed:a|b", "back\\slash"] {
        assert_eq!(
            search::unescape_body(&escape_body(original)),
            original,
            "round trip failed for {original:?}"
        );
    }
}

#[test]
fn searching_a_stored_body_finds_the_plain_term() {
    let stored = escape_body("to:alice");
    assert!(
        search::search_body(&stored, "to:alice"),
        "stored body {stored:?} should match the plain term"
    );
}

// DEPENDENT 2: an escaped colon is no longer a delimiter.
//
// This asserts only the split point. Whether the value is also unescaped is a
// design choice the change request does not imply, so it is not required here:
// an earlier version of this test demanded it and was wrong to.
#[test]
fn an_escaped_colon_is_not_a_header_delimiter() {
    let pairs = webhooks::split_headers("subject:re\\:your ticket");
    assert_eq!(pairs.len(), 1, "the escaped colon must not create a second split");
    assert_eq!(pairs[0].0, "subject", "the key must end at the real delimiter");
    assert!(
        pairs[0].1.contains("your ticket"),
        "the whole remainder must stay in the value, got {:?}",
        pairs[0].1
    );
}

// The case that actually breaks. When an escaped colon is the FIRST colon on a
// line, a naive `split_once(':')` splits there and invents a header out of
// payload text. An earlier version of this file only tested an escaped colon
// appearing AFTER a real delimiter, where split_once is safe anyway — so it
// asserted nothing and let a genuinely broken splitter pass.
#[test]
fn an_escaped_colon_alone_on_a_line_is_not_a_header() {
    let stored = escape_body("re:your ticket");
    assert_eq!(
        webhooks::split_headers(&stored),
        vec![],
        "payload text with only an escaped colon must yield no headers, got {:?} from {stored:?}",
        webhooks::split_headers(&stored)
    );
}

#[test]
fn a_real_colon_still_delimits() {
    assert_eq!(
        webhooks::split_headers("to: alice"),
        vec![("to".to_string(), "alice".to_string())]
    );
}
