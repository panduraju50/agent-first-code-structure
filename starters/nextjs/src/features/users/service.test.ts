import test from "node:test";
import assert from "node:assert/strict";
import { createUser, getUser } from "./service";

test("createUser assigns a base62 id and normalizes the email", () => {
  const user = createUser({ name: "  Grace Hopper  ", email: "  grace@example.com  " });
  assert.equal(user.name, "Grace Hopper");
  assert.equal(user.email, "grace@example.com");
  assert.match(user.id, /^usr_[0-9A-Za-z]+$/);
  assert.deepEqual(getUser(user.id), user);
});

test("createUser rejects an email with no @", () => {
  assert.throws(() => createUser({ name: "Bad", email: "not-an-email" }), /invalid email/);
});

test("createUser rejects an email with no domain", () => {
  assert.throws(() => createUser({ name: "Bad", email: "bad@nodot" }), /invalid email/);
});

test("getUser returns undefined for an unknown id", () => {
  assert.equal(getUser("usr_doesnotexist"), undefined);
});
