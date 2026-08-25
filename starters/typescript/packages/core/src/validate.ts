/**
 * Input validation primitives. This is the ONLY place in the repo allowed
 * to implement title/email validation — domains import these functions
 * rather than re-implementing them (see README.md, "Design D" section).
 */

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

/** Require a non-empty title (after trimming) and return the trimmed value. */
export function validateTitle(title: string): string {
  const trimmed = title.trim();
  if (trimmed.length === 0) {
    throw new ValidationError("title must not be empty");
  }
  return trimmed;
}

// Requires an "@", a non-empty local part, and a domain with at least one dot
// (e.g. "a@b.co"). Intentionally simple: good enough to catch the obvious
// non-email inputs a starter app needs to reject, not a full RFC 5322 parser.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Require a syntactically valid email (at-sign + domain) and return it trimmed. */
export function validateEmail(email: string): string {
  const trimmed = email.trim();
  if (!EMAIL_PATTERN.test(trimmed)) {
    throw new ValidationError(`invalid email address: "${email}"`);
  }
  return trimmed;
}
