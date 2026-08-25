use corelib::ids::short_code;
use corelib::validate::validate_email;

#[derive(Debug, Clone, PartialEq)]
pub struct User {
    pub id: String,
    pub email: String,
}

#[derive(Default)]
pub struct UserStore {
    users: Vec<User>,
    seq: u64,
}

impl UserStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, email: &str) -> Result<User, String> {
        validate_email(email)?;
        if self.users.iter().any(|u| u.email == email.trim()) {
            return Err("email already registered".into());
        }
        self.seq += 1;
        let user = User {
            id: short_code(self.seq),
            email: email.trim().to_string(),
        };
        self.users.push(user.clone());
        Ok(user)
    }

    pub fn get(&self, id: &str) -> Option<&User> {
        self.users.iter().find(|u| u.id == id)
    }

    pub fn count(&self) -> usize {
        self.users.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_user() {
        let mut s = UserStore::new();
        let u = s.create("a@b.com").unwrap();
        assert_eq!(s.get(&u.id).unwrap().email, "a@b.com");
    }

    #[test]
    fn rejects_bad_and_duplicate() {
        let mut s = UserStore::new();
        assert!(s.create("nope").is_err());
        s.create("a@b.com").unwrap();
        assert!(s.create("a@b.com").is_err());
    }
}
