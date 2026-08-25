//! Round 7 — the falsification arm.
//!
//! Rounds 4-6 measured a coupling the contract table *can* express: what
//! characters are escaped. This measures one it cannot.
//!
//! Escaping an additional character makes every stored body containing it
//! longer. `webhooks::accepts` enforces a maximum stored length. Nothing in the
//! escape table mentions length, so the contract object offers no help here —
//! it neither propagates the change nor makes the dependent visible.
//!
//! Prediction: plain and contract score the same. If the contract arm still
//! wins, the explanation offered for rounds 4-6 (that it works by collapsing
//! edit sites for couplings the table expresses) is wrong.
//!
//! The regression criterion is deliberately free of any opinion about HOW to
//! fix it: a body that the endpoint accepted before the change must still be
//! accepted after it. Raising the limit and measuring length before escaping
//! both pass.

use corelib::escape::escape_body;

/// Eleven colons. 21 characters raw, so it fitted the 24-character limit
/// before colons were escaped; 31 characters once each colon becomes `\:`.
const PREVIOUSLY_ACCEPTED: &str = "a:b:c:d:e:f:g:h:i:j:k";

#[test]
fn the_change_actually_lengthens_this_body() {
    // Guards the test itself: if this fails, the fixture stopped exercising
    // the coupling and the rest of the file proves nothing.
    assert!(
        escape_body(PREVIOUSLY_ACCEPTED).len() > PREVIOUSLY_ACCEPTED.len(),
        "fixture no longer grows when escaped"
    );
}

#[test]
fn a_body_accepted_before_the_change_is_still_accepted() {
    let stored = escape_body(PREVIOUSLY_ACCEPTED);
    assert!(
        webhooks::accepts(&stored),
        "a body of {} raw characters was accepted before colons were escaped; \
         escaped it is {} characters and is now rejected",
        PREVIOUSLY_ACCEPTED.len(),
        stored.len()
    );
}

#[test]
fn a_genuinely_oversized_body_is_still_rejected() {
    // The limit must still do its job — "raise it to infinity" is not a fix.
    let huge = "x".repeat(4000);
    assert!(!webhooks::accepts(&huge), "the length limit must still reject");
}

#[test]
fn a_short_body_is_unaffected() {
    assert!(webhooks::accepts(&escape_body("to: alice")));
}
