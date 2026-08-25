//! capability: input-validation
//!
//! Validators used by every domain. Like base62, these live ONLY here;
//! domains call into `corelib::validate`, they never re-implement "is this
//! title non-empty" or "is this email shaped like an email" themselves.

/// capability: title-validation
///
/// A title is valid if it contains at least one non-whitespace character.
pub fn validate_title(title: &str) -> Result<(), String> {
    if title.trim().is_empty() {
        return Err("title must not be empty".to_string());
    }
    Ok(())
}

/// capability: email-validation
///
/// A minimal but real check: requires exactly a local part, an `@`, and a
/// domain part that itself contains a `.` and doesn't start/end with one.
/// This is intentionally not RFC 5322-complete -- it exists to demonstrate
/// "one home for the rule", not to be a production email validator.
pub fn validate_email(email: &str) -> Result<(), String> {
    let at = email
        .find('@')
        .ok_or_else(|| "email must contain '@'".to_string())?;
    let (local, domain) = (&email[..at], &email[at + 1..]);

    if local.is_empty() {
        return Err("email must have a local part before '@'".to_string());
    }
    if domain.is_empty() {
        return Err("email must have a domain after '@'".to_string());
    }
    if !domain.contains('.') || domain.starts_with('.') || domain.ends_with('.') {
        return Err("email domain must contain a '.' and not start/end with one".to_string());
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn title_rejects_empty_or_whitespace() {
        assert!(validate_title("").is_err());
        assert!(validate_title("   ").is_err());
        assert!(validate_title("Buy milk").is_ok());
    }

    #[test]
    fn email_requires_at_sign() {
        assert!(validate_email("no-at-sign").is_err());
    }

    #[test]
    fn email_requires_domain_with_dot() {
        assert!(validate_email("a@").is_err());
        assert!(validate_email("a@b").is_err());
        assert!(validate_email("a@.com").is_err());
        assert!(validate_email("a@b.com").is_ok());
    }
}
