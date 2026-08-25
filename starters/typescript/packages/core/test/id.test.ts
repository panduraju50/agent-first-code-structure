import { test } from "node:test";
import assert from "node:assert/strict";
import { encodeBase62, decodeBase62, nextId } from "../src/id.ts";

test("encodeBase62/decodeBase62 round-trip", () => {
  for (const n of [0, 1, 61, 62, 12345, 999_999_999]) {
    assert.equal(decodeBase62(encodeBase62(n)), BigInt(n));
  }
});

test("encodeBase62 rejects negative values", () => {
  assert.throws(() => encodeBase62(-1), RangeError);
});

test("decodeBase62 rejects invalid characters", () => {
  assert.throws(() => decodeBase62("not-base62!"), RangeError);
});

test("nextId produces unique, prefixed, base62 ids", () => {
  const a = nextId("usr");
  const b = nextId("usr");
  assert.notEqual(a, b);
  assert.match(a, /^usr_[0-9A-Za-z]+$/);
});
