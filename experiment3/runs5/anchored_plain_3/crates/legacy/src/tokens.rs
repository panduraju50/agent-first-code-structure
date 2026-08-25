//! Token helpers for the v1 export path.

const CHARS: &[u8] = b"abcdefghijkmnpqrstuvwxyz23456789";

/// Base32-ish token, ambiguous characters removed.
pub fn make_token(mut n: u64) -> String {
    if n == 0 {
        return "a".to_string();
    }
    let mut out = Vec::new();
    while n > 0 {
        out.push(CHARS[(n % 32) as usize]);
        n /= 32;
    }
    out.reverse();
    String::from_utf8(out).expect("ascii")
}
