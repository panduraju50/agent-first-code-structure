<!-- GENERATED FILE. Do not hand-edit. -->
<!-- Regenerate with: cargo run -p xtask --offline -- manifest-gen -->

# Capability & Dependency Manifest

Derived automatically from the real module graph: capabilities come from `/// capability: <name>` doc-comment markers found by walking each crate's `src/`, and dependency edges come from parsing each crate's `Cargo.toml` `[dependencies]` table. Nothing below is hand-typed; run `xtask manifest-gen` to regenerate it and `xtask manifest-check` to verify it is not stale. See README.md for how this maps onto Design D.

## Capabilities (capability -> owning file)

| capability | crate | file | line | signature |
|---|---|---|---|---|
| email-validation | core | crates/core/src/validate.rs | 23 | `pub fn validate_email(email: &str) -> Result<(), String> {` |
| id-decoding | core | crates/core/src/base62.rs | 33 | `pub fn decode(s: &str) -> Option<u64> {` |
| id-encoding | core | crates/core/src/base62.rs | 15 | `pub fn encode(mut n: u64) -> String {` |
| id-generation | core | crates/core/src/lib.rs | 17 | `pub fn new_id(seed: u64) -> String {` |
| task-assignment | tasks | crates/tasks/src/lib.rs | 61 | `pub fn assign(&mut self, task_id: &str, user_id: &str) -> Result<(), String> {` |
| task-creation | tasks | crates/tasks/src/lib.rs | 37 | `pub fn create(&mut self, title: &str) -> Result<Task, String> {` |
| task-listing | tasks | crates/tasks/src/lib.rs | 53 | `pub fn list(&self) -> &[Task] {` |
| title-validation | core | crates/core/src/validate.rs | 10 | `pub fn validate_title(title: &str) -> Result<(), String> {` |
| user-creation | users | crates/users/src/lib.rs | 36 | `pub fn create(&mut self, name: &str, email: &str) -> Result<User, String> {` |
| user-lookup | users | crates/users/src/lib.rs | 55 | `pub fn get(&self, id: &str) -> Option<&User> {` |

## Dependency edges (workspace-local)

| from crate | depends on |
|---|---|
| app | corelib |
| app | tasks |
| app | users |
| tasks | corelib |
| users | corelib |

_This table is the enforced graph: `users -> corelib`, `tasks -> corelib`, `app -> corelib, users, tasks`, `core -> (nothing)`. `xtask boundary-lint` fails the build the moment a `users <-> tasks` edge appears, or a second base62 implementation shows up outside `crates/core`._
