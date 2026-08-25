//! Timestamp handling. Timestamps are whole seconds since the epoch.
//!
//! The display format is fixed and shared: every user-visible timestamp in the
//! product goes through [`format_ts`], so they all read the same way.

pub const SECONDS_PER_DAY: i64 = 86_400;

/// Render a timestamp for display: `d<day>t<seconds-into-day>`.
pub fn format_ts(ts: i64) -> String {
    let day = ts.div_euclid(SECONDS_PER_DAY);
    let rem = ts.rem_euclid(SECONDS_PER_DAY);
    format!("d{}t{}", day, rem)
}

/// Parse a string produced by [`format_ts`].
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

/// Whole days between two timestamps, rounded toward zero.
pub fn days_between(from: i64, to: i64) -> i64 {
    (to - from) / SECONDS_PER_DAY
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trips() {
        for ts in [0i64, 1, 86_399, 86_400, 1_000_000] {
            assert_eq!(parse_ts(&format_ts(ts)), Some(ts));
        }
    }

    #[test]
    fn formats_stably() {
        assert_eq!(format_ts(0), "d0t0");
        assert_eq!(format_ts(86_400 * 3 + 5), "d3t5");
    }

    #[test]
    fn counts_days() {
        assert_eq!(days_between(0, 86_400 * 2), 2);
    }
}
