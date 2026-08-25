use corelib::ids::short_code;
use corelib::validate::validate_title;

#[derive(Debug, Clone, PartialEq)]
pub struct Webhook {
    pub id: String,
    pub url: String,
    pub secret: String,
}

#[derive(Default)]
pub struct WebhookStore {
    items: Vec<Webhook>,
    seq: u64,
}

impl WebhookStore {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn create(&mut self, url: &str, secret: &str) -> Result<Webhook, String> {
        validate_title(url)?;
        self.seq += 1;
        let item = Webhook {
            id: short_code(self.seq),
            url: url.trim().to_string(),
            secret: secret.trim().to_string(),
        };
        self.items.push(item.clone());
        Ok(item)
    }

    pub fn get(&self, id: &str) -> Option<&Webhook> {
        self.items.iter().find(|i| i.id == id)
    }

    pub fn list(&self) -> &[Webhook] {
        &self.items
    }

    pub fn remove(&mut self, id: &str) -> Result<(), String> {
        let before = self.items.len();
        self.items.retain(|i| i.id != id);
        if self.items.len() == before {
            return Err(format!("no such webhooks: {id}"));
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
        let mut s = WebhookStore::new();
        let item = s.create("sample", "sample").unwrap();
        assert_eq!(s.get(&item.id).map(|i| i.id.clone()), Some(item.id.clone()));
        assert_eq!(s.count(), 1);
    }

    #[test]
    fn removes() {
        let mut s = WebhookStore::new();
        let item = s.create("sample", "sample").unwrap();
        s.remove(&item.id).unwrap();
        assert!(s.get(&item.id).is_none());
        assert!(s.remove("nope").is_err());
    }
}

/// Find the byte index of the first ':' in `line` that is not escaped with
/// a preceding backslash (matching `corelib::escape::escape_body`'s scheme,
/// where a backslash escapes whatever character follows it).
fn find_unescaped_colon(line: &str) -> Option<usize> {
    let mut chars = line.char_indices();
    while let Some((idx, c)) = chars.next() {
        if c == '\\' {
            chars.next();
            continue;
        }
        if c == ':' {
            return Some(idx);
        }
    }
    None
}

/// Split a stored notification body into its `key:value` header pairs.
/// A ':' inside the payload itself is not a delimiter once it is escaped.
pub fn split_headers(stored_body: &str) -> Vec<(String, String)> {
    stored_body
        .split('\n')
        .filter_map(|line| {
            let idx = find_unescaped_colon(line)?;
            Some((&line[..idx], &line[idx + 1..]))
        })
        .map(|(k, v)| (k.trim().to_string(), v.trim().to_string()))
        .collect()
}

#[cfg(test)]
mod header_tests {
    use super::*;

    #[test]
    fn splits_on_the_first_colon() {
        let pairs = split_headers("to: alice");
        assert_eq!(pairs, vec![("to".to_string(), "alice".to_string())]);
    }

    #[test]
    fn ignores_escaped_colons_in_the_value() {
        let pairs = split_headers("time: 10\\:30");
        assert_eq!(pairs, vec![("time".to_string(), "10\\:30".to_string())]);
    }
}
