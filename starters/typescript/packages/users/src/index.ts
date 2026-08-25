// Domain module: users.
//
// Design D rule: this file may depend on core, but MUST NOT import from
// ../../tasks. Assignment is done by passing a plain user id string across
// the boundary (see packages/tasks/src/index.ts#assignTask) instead of
// importing the User type — that is how two domains stay decoupled while
// still cooperating. tools/boundary-lint.mjs fails the build if this file
// ever imports anything under packages/tasks.
import { nextId } from "../../core/src/id.ts";
import { validateEmail } from "../../core/src/validate.ts";
import type { User } from "./types.ts";

const usersById = new Map<string, User>();

/** Create and store a new user. Throws ValidationError on a bad email. */
export function createUser(name: string, email: string): User {
  const cleanEmail = validateEmail(email);
  const user: User = { id: nextId("usr"), name, email: cleanEmail };
  usersById.set(user.id, user);
  return user;
}

/** Look up a previously created user by id. */
export function getUser(id: string): User | undefined {
  return usersById.get(id);
}

export type { User };
