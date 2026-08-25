// Composition root.
//
// Design D rule: packages/app is the ONE place in the repo allowed to
// import across domains (users AND tasks). It wires them together and
// runs the scenario below. No other package may do this — see
// packages/users/tsconfig.json and packages/tasks/tsconfig.json, whose
// `references` arrays each list only ../core, and tools/boundary-lint.mjs,
// which enforces the same rule at the source-text level.
import { createUser, getUser } from "../../users/src/index.ts";
import { createTask, listTasks, assignTask } from "../../tasks/src/index.ts";

function main(): void {
  const alice = createUser("Alice", "alice@example.com");
  const bob = createUser("Bob", "bob@example.com");

  const readme = createTask("Write the Design D README");
  const ci = createTask("Wire the boundary enforcer into CI");

  assignTask(readme.id, alice.id);
  assignTask(ci.id, bob.id);

  console.log("Users:");
  for (const id of [alice.id, bob.id]) {
    console.log(" -", getUser(id));
  }

  console.log("Tasks:");
  for (const task of listTasks()) {
    console.log(" -", task);
  }
}

main();
