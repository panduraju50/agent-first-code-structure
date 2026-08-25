use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Comment {
    pub id: String,
    pub body: String,
    pub author: String,
}

#[derive(Default)]
pub struct CommentStore {
    items: Vec<Comment>,
    seq: u64,
}

impl CommentStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, body: &str, author: &str) -> Result<Comment, String> {
        validate_title(body)?;
        self.seq += 1;
        let item = Comment {
            id: short_code(self.seq),
            body: body.trim().to_string(),
            author: author.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Comment> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Comment] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such comments: {id}"));
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
        let mut s = CommentStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = CommentStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}
