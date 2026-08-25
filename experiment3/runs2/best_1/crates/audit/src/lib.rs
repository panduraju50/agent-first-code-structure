use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct AuditEntry {
    pub id: String,
    pub action: String,
    pub actor: String,
}

#[derive(Default)]
pub struct AuditEntryStore {
    items: Vec<AuditEntry>,
    seq: u64,
}

impl AuditEntryStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, action: &str, actor: &str) -> Result<AuditEntry, String> {
        validate_title(action)?;
        self.seq += 1;
        let item = AuditEntry {
            id: short_code(self.seq),
            action: action.trim().to_string(),
            actor: actor.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&AuditEntry> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[AuditEntry] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such audit: {id}"));
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
        let mut s = AuditEntryStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = AuditEntryStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
