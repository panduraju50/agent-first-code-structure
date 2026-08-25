// @capability core.id.base62
//
// The ONE home for base62 id encoding in this repo. Every feature that needs
// an id imports `nextId`/`toBase62` from here instead of writing its own
// encoder. `scripts/check-boundaries.mjs` fails the build if any file outside
// `src/core` defines something that looks like a base62 encoder.

const ALPHABET =
  "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

export function toBase62(value: number): string {
  if (!Number.isInteger(value) || value < 0) {
    throw new RangeError(`toBase62 expects a non-negative integer, got ${value}`);
  }
  if (value === 0) {
    return "0";
  }
  let out = "";
  let remaining = value;
  while (remaining > 0) {
    const digit = remaining % 62;
    out = ALPHABET[digit] + out;
    remaining = Math.floor(remaining / 62);
  }
  return out;
}

let counter = 0;

/**
 * A short, prefixed, base62-encoded id. Not cryptographically random — good
 * enough for an in-memory demo, and the only place this repo generates ids.
 */
export function nextId(prefix: string): string {
  counter += 1;
  const stamp = Date.now() % 1_000_000_000;
  return `${prefix}_${toBase62(stamp)}${toBase62(counter)}`;
}
