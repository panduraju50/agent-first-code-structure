/**
 * Base62 id encoding. This is the ONLY place in the repo allowed to
 * implement a base62 encoder/decoder or an id generator — see
 * tools/boundary-lint.mjs and .dependency-cruiser.js, which both fail the
 * build if another file defines a lookalike primitive.
 */

const ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
const BASE = BigInt(ALPHABET.length);

/** Encode a non-negative integer as a base62 string. */
export function encodeBase62(value: number | bigint): string {
  let n = BigInt(value);
  if (n < 0n) {
    throw new RangeError("encodeBase62: value must be non-negative");
  }
  if (n === 0n) {
    return ALPHABET[0]!;
  }
  let out = "";
  while (n > 0n) {
    const remainder = Number(n % BASE);
    out = ALPHABET[remainder]! + out;
    n = n / BASE;
  }
  return out;
}

/** Decode a base62 string back into its integer value. */
export function decodeBase62(input: string): bigint {
  if (input.length === 0) {
    throw new RangeError("decodeBase62: input must not be empty");
  }
  let n = 0n;
  for (const char of input) {
    const digit = ALPHABET.indexOf(char);
    if (digit === -1) {
      throw new RangeError(`decodeBase62: invalid base62 character '${char}'`);
    }
    n = n * BASE + BigInt(digit);
  }
  return n;
}

let sequence = 0n;

/**
 * Generate a short, sortable, base62-encoded id with a domain prefix
 * (e.g. "usr_", "tsk_"). Combines the current time with a monotonic
 * counter so ids created in the same millisecond stay unique.
 */
export function nextId(prefix: string): string {
  sequence = (sequence + 1n) % 0x100000n; // wrap the low 20 bits
  const millis = BigInt(Date.now());
  const value = (millis << 20n) | sequence;
  return `${prefix}_${encodeBase62(value)}`;
}
