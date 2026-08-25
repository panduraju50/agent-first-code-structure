use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Label {
    pub id: String,
    pub name: String,
    pub kind: String,
}

#[derive(Default)]
pub struct LabelStore {
    items: Vec<Label>,
    seq: u64,
}

impl LabelStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, name: &str, kind: &str) -> Result<Label, String> {
        validate_title(name)?;
        self.seq += 1;
        let item = Label {
            id: short_code(self.seq),
            name: name.trim().to_string(),
            kind: kind.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Label> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Label] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such labels: {id}"));
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
        let mut s = LabelStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = LabelStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
