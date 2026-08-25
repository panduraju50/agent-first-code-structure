//! Older presentation helpers retained for the v1 export path.

/// Human-ish rendering used by the v1 CSV export.
pub fn render_time(ts: i64) -> String {
    let days = ts / 86_400;
    let hours = (ts % 86_400) / 3_600;
    format!("{days} days {hours}h")
}

pub fn render_flag(on: bool) -> &'static str {
    if on {
        "yes"
    } else {
        "no"
    }
}
