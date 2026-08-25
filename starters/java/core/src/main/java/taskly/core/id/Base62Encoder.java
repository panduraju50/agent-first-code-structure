package taskly.core.id;

/**
 * The ONE home for base62 id encoding in this repository.
 *
 * Design D rule: no other module may define an alphabet, an encode/decode
 * routine, or any other "id formatting" primitive. Domains that need ids
 * call {@link #encode(long)} from here. tools/BoundaryCheck enforces that
 * no such definition exists outside this file.
 */
public final class Base62Encoder {

    private static final String ALPHABET =
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    private static final int BASE = ALPHABET.length();

    private Base62Encoder() {
    }

    /** Encodes a non-negative long as a base62 string. Zero encodes as "0". */
    public static String encode(long value) {
        if (value < 0) {
            throw new IllegalArgumentException("value must be non-negative: " + value);
        }
        if (value == 0) {
            return "0";
        }
        StringBuilder out = new StringBuilder();
        long remaining = value;
        while (remaining > 0) {
            int digit = (int) (remaining % BASE);
            out.append(ALPHABET.charAt(digit));
            remaining /= BASE;
        }
        return out.reverse().toString();
    }

    /** Decodes a base62 string produced by {@link #encode(long)} back to a long. */
    public static long decode(String text) {
        if (text == null || text.isEmpty()) {
            throw new IllegalArgumentException("text must not be empty");
        }
        long value = 0;
        for (int i = 0; i < text.length(); i++) {
            int digit = ALPHABET.indexOf(text.charAt(i));
            if (digit < 0) {
                throw new IllegalArgumentException("not a base62 character: " + text.charAt(i));
            }
            value = value * BASE + digit;
        }
        return value;
    }
}
