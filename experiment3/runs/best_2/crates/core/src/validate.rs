//! Input validation. All user-supplied text is checked here.

/// A title must be non-blank and at most 200 characters.
pub fn validate_title(title: &str) -> Result<(), String> {
    let t = title.trim();
    if t.is_empty() {
        return Err("title must not be blank".into());
    }
    if t.chars().count() > 200 {
        return Err("title must be at most 200 characters".into());
    }
    Ok(())
}

/// An email must have a local part, an `@`, and a dotted domain.
pub fn validate_email(email: &str) -> Result<(), String> {
    let e = email.trim();
    let (local, domain) = e.split_once('@').ok_or("email must contain '@'")?;
    if local.is_empty() {
        return Err("email must have a local part".into());
    }
    if !domain.contains('.') || domain.starts_with('.') || domain.ends_with('.') {
        return Err("email must have a valid domain".into());
    }
    Ok(())
}

/// A timestamp must not be negative.
pub fn validate_timestamp(ts: i64) -> Result<(), String> {
    if ts < 0 {
        return Err(format!("timestamp cannot be negative: {ts}"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn titles() {
        assert!(validate_title("write docs").is_ok());
        assert!(validate_title("   ").is_err());
    }

    #[test]
    fn emails() {
        assert!(validate_email("a@b.com").is_ok());
        assert!(validate_email("nope").is_err());
        assert!(validate_email("@b.com").is_err());
    }

    #[test]
    fn timestamps() {
        assert!(validate_timestamp(0).is_ok());
        assert!(validate_timestamp(1_000).is_ok());
        assert!(validate_timestamp(-1).is_err());
    }
}
