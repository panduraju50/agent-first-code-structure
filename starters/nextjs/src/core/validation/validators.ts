// The ONE home for input validation primitives. Domains call these; they must
// never re-implement title/email validation locally (the boundary enforcer
// checks for exactly that).

// @capability core.validation.title
export function validateTitle(title: string): string {
  const trimmed = title.trim();
  if (trimmed.length === 0) {
    throw new Error("title must not be empty");
  }
  return trimmed;
}

// A deliberately simple but real check: requires an "@" AND a "." in the
// domain part, so "not-an-email" and "user@nodot" are both rejected while
// "user@example.com" passes.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// @capability core.validation.email
export function validateEmail(email: string): string {
  const trimmed = email.trim();
  if (!EMAIL_RE.test(trimmed)) {
    throw new Error(`invalid email: ${email}`);
  }
  return trimmed;
}
