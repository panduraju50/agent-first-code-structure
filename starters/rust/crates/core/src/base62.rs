//! capability: id-encoding
//!
//! Base62 encoder/decoder. This is the ONE home for this primitive in the
//! entire workspace (Design D, rule 1). `xtask boundary-lint` fails the
//! build if it finds a second base62 implementation anywhere outside
//! `crates/core`.

const ALPHABET: &[u8] = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

/// capability: id-encoding
///
/// Encode a `u64` as a base62 string. Domains never re-implement this; they
/// call `corelib::base62::encode` (or the `corelib::new_id` convenience
/// wrapper).
pub fn encode(mut n: u64) -> String {
    if n == 0 {
        return "0".to_string();
    }
    let mut buf = Vec::new();
    while n > 0 {
        let rem = (n % 62) as usize;
        buf.push(ALPHABET[rem]);
        n /= 62;
    }
    buf.reverse();
    String::from_utf8(buf).expect("alphabet is ascii")
}

/// capability: id-decoding
///
/// Decode a base62 string back into a `u64`. Returns `None` on any
/// character outside the base62 alphabet or on overflow.
pub fn decode(s: &str) -> Option<u64> {
    let mut n: u64 = 0;
    for c in s.bytes() {
        let digit = ALPHABET.iter().position(|&a| a == c)? as u64;
        n = n.checked_mul(62)?.checked_add(digit)?;
    }
    Some(n)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        for n in [0u64, 1, 61, 62, 12345, u64::MAX] {
            let s = encode(n);
            assert_eq!(decode(&s), Some(n), "roundtrip failed for {n}");
        }
    }

    #[test]
    fn zero_encodes_to_zero_char() {
        assert_eq!(encode(0), "0");
    }

    #[test]
    fn decode_rejects_bad_characters() {
        assert_eq!(decode("not!valid"), None);
    }
}
