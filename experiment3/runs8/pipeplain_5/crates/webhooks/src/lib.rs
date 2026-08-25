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
/// A ':' inside the payload itself is not a delimiter once it is escaped.
pub fn split_headers(stored_body: &str) -> Vec<(String, String)> {
    stored_body
        .split('\n')
        .filter_map(split_at_unescaped_colon)
        .map(|(k, v)| (k.trim().to_string(), v.trim().to_string()))
        .collect()
}

/// Find the first ':' in `line` that is not escaped (i.e. not immediately
/// preceded by a backslash) and split the line there. A backslash always
/// escapes the character that follows it, so `\:` never matches.
fn split_at_unescaped_colon(line: &str) -> Option<(&str, &str)> {
    let mut escaped = false;
    for (idx, ch) in line.char_indices() {
        if escaped {
            escaped = false;
            continue;
        }
        match ch {
            '\\' => escaped = true,
            ':' => return Some((&line[..idx], &line[idx + ch.len_utf8()..])),
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
    fn escaped_colon_is_not_a_delimiter() {
        // Once ':' has been escaped (as produced by corelib::escape::escape_body),
        // an escaped colon in the payload must not be mistaken for the
        // key:value delimiter.
        let pairs = split_headers("note\\: not a header");
        assert_eq!(pairs, Vec::<(String, String)>::new());
    }

    #[test]
    fn real_delimiter_still_splits_around_an_escaped_colon_in_the_value() {
        let pairs = split_headers("to: a\\:b");
        assert_eq!(pairs, vec![("to".to_string(), "a\\:b".to_string())]);
    }
}

/// Maximum stored body length accepted by the v1 delivery endpoint.
pub const MAX_STORED_BODY: usize = 24;

/// Reject a stored body the delivery endpoint cannot carry.
pub fn accepts(stored_body: &str) -> bool {
    stored_body.len() <= MAX_STORED_BODY
}

#[cfg(test)]
mod length_tests {
    use super::*;

    #[test]
    fn accepts_a_short_body() {
        assert!(accepts("to: alice"));
    }
}
