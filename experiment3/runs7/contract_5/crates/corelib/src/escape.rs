//! The escaping contract.
//!
//! Everything about escaping is derived from ONE table. Encoder, decoder and
//! delimiter-scanner all read it, so they cannot disagree: adding a character
//! is a single line, and every party updates mechanically.
//!
//! The invariants that bind those parties are exported as runnable checks, so a
//! consumer can assert the contract against its own usage rather than trusting
//! a comment.

/// (character, the letter it is escaped as). A backslash precedes the letter.
pub type Escape = (char, char);

/// The single definition of how a notification body is escaped.
///
/// To escape another character, add one row. Nothing else changes.
pub const BODY: Scheme = Scheme {
    escapes: &[('\\', '\\'), ('|', '|'), ('\n', 'n'), (':', ':')],
};

pub struct Scheme {
    escapes: &'static [Escape],
}

impl Scheme {
    fn letter_for(&self, c: char) -> Option<char> {
        self.escapes.iter().find(|(raw, _)| *raw == c).map(|(_, l)| *l)
    }

    fn raw_for(&self, letter: char) -> Option<char> {
        self.escapes.iter().find(|(_, l)| *l == letter).map(|(raw, _)| *raw)
    }

    /// True when this character is escaped by the scheme, so an unescaped
    /// occurrence of it is structurally significant.
    pub fn is_escaped(&self, c: char) -> bool {
        self.letter_for(c).is_some()
    }

    pub fn encode(&self, s: &str) -> String {
        let mut out = String::with_capacity(s.len());
        for c in s.chars() {
            match self.letter_for(c) {
                Some(letter) => {
                    out.push('\\');
                    out.push(letter);
                }
                None => out.push(c),
            }
        }
        out
    }

    pub fn decode(&self, s: &str) -> String {
        let mut out = String::with_capacity(s.len());
        let mut chars = s.chars();
        while let Some(c) = chars.next() {
            if c != '\\' {
                out.push(c);
                continue;
            }
            match chars.next() {
                Some(letter) => match self.raw_for(letter) {
                    Some(raw) => out.push(raw),
                    None => {
                        out.push('\\');
                        out.push(letter);
                    }
                },
                None => out.push('\\'),
            }
        }
        out
    }

    /// Byte index of the first `needle` that the scheme did NOT escape — i.e.
    /// the first structurally significant occurrence. A parser asking "where
    /// does the delimiter really start" asks here, so it can never disagree
    /// with the encoder about what counts as escaped.
    pub fn first_unescaped(&self, s: &str, needle: char) -> Option<usize> {
        let mut escaped = false;
        for (i, c) in s.char_indices() {
            if escaped {
                escaped = false;
                continue;
            }
            if c == '\\' {
                escaped = true;
                continue;
            }
            if c == needle {
                return Some(i);
            }
        }
        None
    }

    /// The contract itself, executable. A consumer runs this against its own
    /// inputs instead of trusting that encode and decode still agree.
    pub fn assert_round_trip(&self, sample: &str) {
        assert_eq!(
            self.decode(&self.encode(sample)),
            sample,
            "round trip failed for {sample:?}"
        );
    }

    /// Every string built from the scheme's own alphabet, up to `len`.
    /// Generated from the table, so it automatically covers characters added
    /// later — the check cannot fall behind the contract.
    pub fn exhaustive_samples(&self, len: usize) -> Vec<String> {
        let mut alphabet: Vec<char> = self.escapes.iter().map(|(raw, _)| *raw).collect();
        alphabet.push('a');
        let mut cases = vec![String::new()];
        for _ in 0..len {
            let mut next = Vec::new();
            for base in &cases {
                for c in &alphabet {
                    let mut s = base.clone();
                    s.push(*c);
                    next.push(s);
                }
            }
            cases.extend(next);
        }
        cases
    }
}

/// Kept so existing callers do not change.
pub fn escape_body(s: &str) -> String {
    BODY.encode(s)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips_every_string_over_its_own_alphabet() {
        for s in BODY.exhaustive_samples(3) {
            BODY.assert_round_trip(&s);
        }
    }

    #[test]
    fn an_escaped_character_is_never_seen_as_a_delimiter() {
        for s in BODY.exhaustive_samples(3) {
            let encoded = BODY.encode(&s);
            for (raw, _) in BODY.escapes {
                if let Some(i) = BODY.first_unescaped(&encoded, *raw) {
                    panic!("encoded {encoded:?} still exposes {raw:?} at {i}");
                }
            }
        }
    }
}
