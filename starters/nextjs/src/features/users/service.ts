// The `users` domain depends on `core` only — never on `tasks`. Importing
// `../../features/tasks` from here would be caught by both the
// eslint-plugin-boundaries config and scripts/check-boundaries.mjs.
import { nextId, validateEmail } from "../../core";
import type { User } from "./types";
import { saveUser, findUser } from "./repository";

// @capability users.create
export function createUser(input: { name: string; email: string }): User {
  const email = validateEmail(input.email);
  const user: User = { id: nextId("usr"), email, name: input.name.trim() };
  return saveUser(user);
}

// @capability users.get
export function getUser(id: string): User | undefined {
  return findUser(id);
}
