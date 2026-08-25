// The composition root: the ONE file in this repo allowed to import both
// `users` and `tasks`. This is where the two domains actually get wired
// together (e.g. checking a user exists before assigning them a task) —
// logic that must never leak into either feature, since that would create
// the users<->tasks edge Design D forbids.
//
// @capability composition.root
import { createUser, getUser, type User } from "../features/users";
import { createTask, listTasks, assignTask, type Task } from "../features/tasks";

export interface Scenario {
  user: User;
  tasks: Task[];
}

export function runScenario(): Scenario {
  const user = createUser({ name: "Ada Lovelace", email: "ada@example.com" });

  createTask({ title: "Write the boundary enforcer" });
  createTask({ title: "Draft the README" });

  const [first] = listTasks();

  // The cross-domain invariant ("does this assignee actually exist?") is
  // enforced HERE, in the one place that can see both domains — not inside
  // `tasks`, which has no way to ask `users` anything.
  if (!first) {
    throw new Error("composition invariant violated: no tasks to assign");
  }
  if (!getUser(user.id)) {
    throw new Error("composition invariant violated: user not found after creation");
  }
  assignTask(first.id, user.id);

  return { user, tasks: listTasks() };
}
