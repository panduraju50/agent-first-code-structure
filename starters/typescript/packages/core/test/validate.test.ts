import { test } from "node:test";
import assert from "node:assert/strict";
import { validateTitle, validateEmail, ValidationError } from "../src/validate.ts";

test("validateTitle rejects empty and whitespace-only titles", () => {
  assert.throws(() => validateTitle(""), ValidationError);
  assert.throws(() => validateTitle("   "), ValidationError);
});

test("validateTitle trims and returns a valid title", () => {
  assert.equal(validateTitle("  Write docs  "), "Write docs");
});

test("validateEmail requires an at-sign and a domain", () => {
  assert.throws(() => validateEmail("not-an-email"), ValidationError, "no at-sign");
  assert.throws(() => validateEmail("missing-domain@"), ValidationError, "no domain");
  assert.throws(() => validateEmail("@missing-local.com"), ValidationError, "no local part");
  assert.throws(() => validateEmail("no-dot@domain"), ValidationError, "no dot in domain");
});

test("validateEmail accepts a well-formed address", () => {
  assert.equal(validateEmail(" a@b.co "), "a@b.co");
});
