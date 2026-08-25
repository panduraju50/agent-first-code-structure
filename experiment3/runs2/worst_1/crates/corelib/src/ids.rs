//! Reference code helpers.

const ALPHABET: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

pub fn short_code(mut n: u64) -> String {
    if n == 0 {
        return "0".to_string();
    }
    let mut out = Vec::new();
    while n > 0 {
        out.push(ALPHABET[(n % 62) as usize]);
        n /= 62;
    }
    out.reverse();
    String::from_utf8(out).expect("ascii")
}

pub fn decode_code(s: &str) -> Option<u64> {
    let mut n: u64 = 0;
    for b in s.bytes() {
        let idx = ALPHABET.iter().position(|&c| c == b)?;
        n = n.checked_mul(62)?.checked_add(idx as u64)?;
    }
    Some(n)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        for n in [0u64, 1, 61, 62, 4000] {
            assert_eq!(decode_code(&short_code(n)), Some(n));
        }
    }
}
