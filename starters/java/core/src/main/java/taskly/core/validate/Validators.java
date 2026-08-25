package taskly.core.validate;

import java.util.regex.Pattern;

/**
 * The ONE home for input validation primitives in this repository.
 *
 * Design D rule: "non-empty" checks and "email" checks are defined exactly
 * once, here. taskly.users reuses {@link #requireEmail(String)} for its
 * emails and {@link #requireNonEmpty(String, String)} for names; taskly.tasks
 * reuses {@link #requireNonEmpty(String, String)} for task titles. Neither
 * domain is allowed to redefine these checks — tools/BoundaryCheck fails the
 * build if it finds a duplicate definition outside this file.
 */
public final class Validators {

    // Requires an "@", at least one character on each side of it, and a
    // domain with a dot (so "a@b" is rejected but "a@b.co" is accepted).
    private static final Pattern EMAIL =
            Pattern.compile("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$");

    private Validators() {
    }

    /** Trims and requires a non-empty value; used for titles, names, etc. */
    public static String requireNonEmpty(String value, String fieldName) {
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(fieldName + " must not be empty");
        }
        return value.trim();
    }

    /** Requires a syntactically valid email: local-part "@" domain "." tld. */
    public static String requireEmail(String email) {
        String trimmed = requireNonEmpty(email, "email");
        if (!EMAIL.matcher(trimmed).matches()) {
            throw new IllegalArgumentException("email is not valid: " + email);
        }
        return trimmed;
    }
}
