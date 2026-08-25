//! Cross-cutting primitives. Every one of these has exactly one home here;
//! domain crates depend on this crate rather than re-implementing them.

pub mod ids;
pub mod timefmt;
pub mod validate;
