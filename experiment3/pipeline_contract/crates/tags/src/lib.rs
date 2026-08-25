use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Tag {
    pub id: String,
    pub label: String,
    pub colour: String,
}

#[derive(Default)]
pub struct TagStore {
    items: Vec<Tag>,
    seq: u64,
}

impl TagStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, label: &str, colour: &str) -> Result<Tag, String> {
        validate_title(label)?;
        self.seq += 1;
        let item = Tag {
            id: short_code(self.seq),
            label: label.trim().to_string(),
            colour: colour.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Tag> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Tag] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such tags: {id}"));
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
        let mut s = TagStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = TagStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
