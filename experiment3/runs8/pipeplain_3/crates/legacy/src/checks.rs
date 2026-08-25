//! Older bounds checks. Exclusive upper bound.

pub fn in_bounds(value: i64, lo: i64, hi: i64) -> bool {
    value >= lo && value < hi
}
