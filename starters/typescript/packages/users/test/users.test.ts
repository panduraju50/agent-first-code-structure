import { test } from "node:test";
import assert from "node:assert/strict";
import { createUser, getUser } from "../src/index.ts";
import { ValidationError } from "../../core/src/validate.ts";

test("createUser stores a retrievable user with a base62 id", () => {
  const user = createUser("Carol", "carol@example.com");
  assert.match(user.id, /^usr_[0-9A-Za-z]+$/);
  assert.equal(getUser(user.id)?.email, "carol@example.com");
});

test("createUser rejects an invalid email via core's validator", () => {
  assert.throws(() => createUser("Dave", "not-an-email"), ValidationError);
});

test("getUser returns undefined for an unknown id", () => {
  assert.equal(getUser("usr_doesNotExist"), undefined);
});
