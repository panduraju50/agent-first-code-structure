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

/// Split a stored notification body into its `key:value` header pairs.
/// A ':' inside the payload itself is not a delimiter once it is escaped
/// (as `\:`).
pub fn split_headers(stored_body: &str) -> Vec<(String, String)> {
    stored_body
        .split('\n')
        .filter_map(split_on_first_unescaped_colon)
        .map(|(k, v)| (k.trim().to_string(), v.trim().to_string()))
        .collect()
}

/// Like `str::split_once(':')`, but a `:` preceded by an unescaped `\` is
/// treated as literal payload rather than a delimiter.
fn split_on_first_unescaped_colon(line: &str) -> Option<(&str, &str)> {
    let mut escaped = false;
    for (idx, c) in line.char_indices() {
        if escaped {
            escaped = false;
            continue;
        }
        match c {
            '\\' => escaped = true,
            ':' => return Some((&line[..idx], &line[idx + c.len_utf8()..])),
            _ => {}
        }
    }
    None
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
    fn ignores_an_escaped_colon_in_the_payload() {
        let pairs = split_headers("to: a\\:b");
        assert_eq!(pairs, vec![("to".to_string(), "a\\:b".to_string())]);
    }
}
