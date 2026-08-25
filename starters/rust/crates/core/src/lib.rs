//! `corelib` -- the ONE home for cross-cutting primitives (Design D, rule 1).
//!
//! This crate has zero workspace dependencies (see `Cargo.toml`): it sits
//! at the bottom of the dependency graph. Both domain crates (`users`,
//! `tasks`) depend on it; it never depends on them, directly or
//! transitively. `xtask boundary-lint` asserts this from the real
//! `Cargo.toml` files on every run.

pub mod base62;
pub mod validate;

/// capability: id-generation
///
/// Convenience wrapper combining a seed with the base62 encoder. Exists so
/// that "how do I make an id" has exactly one answer in the workspace,
/// instead of every domain writing its own `format!("{n:x}")`.
pub fn new_id(seed: u64) -> String {
    base62::encode(seed)
}
