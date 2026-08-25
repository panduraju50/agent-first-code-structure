// In-memory persistence for the `users` domain. Server-only: never imported
// by a "use client" component (the boundary enforcer checks this too, via
// the composition/app edge rules — app never reaches into features directly).
import type { User } from "./types";

const users = new Map<string, User>();

export function saveUser(user: User): User {
  users.set(user.id, user);
  return user;
}

export function findUser(id: string): User | undefined {
  return users.get(id);
}

export function allUsers(): User[] {
  return Array.from(users.values());
}
