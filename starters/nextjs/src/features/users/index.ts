// Public barrel for the `users` domain — the only surface the composition
// root (or anything else) is allowed to import from.
export type { User } from "./types";
export { createUser, getUser } from "./service";
