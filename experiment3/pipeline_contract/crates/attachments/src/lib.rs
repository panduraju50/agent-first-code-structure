use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Attachment {
    pub id: String,
    pub filename: String,
    pub mime: String,
}

#[derive(Default)]
pub struct AttachmentStore {
    items: Vec<Attachment>,
    seq: u64,
}

impl AttachmentStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, filename: &str, mime: &str) -> Result<Attachment, String> {
        validate_title(filename)?;
        self.seq += 1;
        let item = Attachment {
            id: short_code(self.seq),
            filename: filename.trim().to_string(),
            mime: mime.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Attachment> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Attachment] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such attachments: {id}"));
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
        let mut s = AttachmentStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = AttachmentStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
