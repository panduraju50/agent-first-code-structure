//! `users` -- a domain module (Design D, rule 2).
//!
//! Depends on `corelib` only (see `Cargo.toml`). Must never depend on the
//! `tasks` domain, and never re-implements id encoding or email
//! validation -- both come from `corelib`.

use corelib::new_id;
use corelib::validate::validate_email;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct User {
    pub id: String,
    pub name: String,
    pub email: String,
}

#[derive(Debug, Default)]
pub struct UserStore {
    users: Vec<User>,
    next_seed: u64,
}

impl UserStore {
    pub fn new() -> Self {
        Self {
            users: Vec::new(),
            next_seed: 1,
        }
    }

    /// capability: user-creation
    ///
    /// Validates `email` via `corelib::validate::validate_email` and mints
    /// the id via `corelib::new_id` -- both borrowed from core, never
    /// reimplemented here.
    pub fn create(&mut self, name: &str, email: &str) -> Result<User, String> {
        if name.trim().is_empty() {
            return Err("name must not be empty".to_string());
        }
        validate_email(email)?;

        let id = new_id(self.next_seed);
        self.next_seed += 1;

        let user = User {
            id,
            name: name.to_string(),
            email: email.to_string(),
        };
        self.users.push(user.clone());
        Ok(user)
    }

    /// capability: user-lookup
    pub fn get(&self, id: &str) -> Option<&User> {
        self.users.iter().find(|u| u.id == id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn create_and_get_roundtrip() {
        let mut store = UserStore::new();
        let created = store.create("Ada Lovelace", "ada@example.com").unwrap();
        let found = store.get(&created.id).expect("just-created user must be found");
        assert_eq!(found, &created);
    }

    #[test]
    fn rejects_invalid_email_via_core_validator() {
        let mut store = UserStore::new();
        let err = store.create("Ada", "not-an-email").unwrap_err();
        assert!(err.contains('@'), "error should mention the missing '@': {err}");
    }

    #[test]
    fn rejects_empty_name() {
        let mut store = UserStore::new();
        assert!(store.create("   ", "ada@example.com").is_err());
    }

    #[test]
    fn get_unknown_id_returns_none() {
        let store = UserStore::new();
        assert_eq!(store.get("does-not-exist"), None);
    }
}
