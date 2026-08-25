//! Input validation.

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

/// Check that `value` falls within `lo..=hi`, naming the field in the error.
pub fn validate_range(field: &str, value: i64, lo: i64, hi: i64) -> Result<(), String> {
    if value < lo || value > hi {
        return Err(format!("{field} must be between {lo} and {hi}"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ranges() {
        assert!(validate_range("window", 5, 0, 10).is_ok());
        assert_eq!(
            validate_range("window", 11, 0, 10).unwrap_err(),
            "window must be between 0 and 10"
        );
    }
}
