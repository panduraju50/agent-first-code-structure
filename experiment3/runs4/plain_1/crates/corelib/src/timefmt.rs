//! Timestamp helpers.

pub const SECONDS_PER_DAY: i64 = 86_400;

pub fn format_ts(ts: i64) -> String {
    let day = ts.div_euclid(SECONDS_PER_DAY);
    let rem = ts.rem_euclid(SECONDS_PER_DAY);
    format!("d{}t{}", day, rem)
}

pub fn parse_ts(s: &str) -> Option<i64> {
    let rest = s.strip_prefix('d')?;
    let (day, secs) = rest.split_once('t')?;
    let day: i64 = day.parse().ok()?;
    let secs: i64 = secs.parse().ok()?;
    if !(0..SECONDS_PER_DAY).contains(&secs) {
        return None;
    }
    Some(day * SECONDS_PER_DAY + secs)
}

pub fn days_between(from: i64, to: i64) -> i64 {
    (to - from).div_euclid(SECONDS_PER_DAY)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        for ts in [0i64, 1, 86_399, 86_400] {
            assert_eq!(parse_ts(&format_ts(ts)), Some(ts));
        }
    }
}
