use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Team {
    pub id: String,
    pub name: String,
    pub lead: String,
}

#[derive(Default)]
pub struct TeamStore {
    items: Vec<Team>,
    seq: u64,
}

impl TeamStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, name: &str, lead: &str) -> Result<Team, String> {
        validate_title(name)?;
        self.seq += 1;
        let item = Team {
            id: short_code(self.seq),
            name: name.trim().to_string(),
            lead: lead.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Team> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Team] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such teams: {id}"));
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
        let mut s = TeamStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = TeamStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
