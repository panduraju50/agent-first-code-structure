use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub owner: String,
}

#[derive(Default)]
pub struct ProjectStore {
    items: Vec<Project>,
    seq: u64,
}

impl ProjectStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, name: &str, owner: &str) -> Result<Project, String> {
        validate_title(name)?;
        self.seq += 1;
        let item = Project {
            id: short_code(self.seq),
            name: name.trim().to_string(),
            owner: owner.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Project> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Project] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such projects: {id}"));
        }
        Ok(())
    }

    pub fn count(&self) -> usize {
        self.items.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_and_reads() {
        let mut s = ProjectStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = ProjectStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
