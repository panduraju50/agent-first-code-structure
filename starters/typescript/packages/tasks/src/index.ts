// Domain module: tasks.
//
// Design D rule: this file may depend on core, but MUST NOT import from
// ../../users. assignTask takes a raw user-id string, not a User object —
// tasks never needs to know how users are represented, so there is no
// users-to-tasks (or tasks-to-users) edge in the module graph.
// tools/boundary-lint.mjs fails the build if this file ever imports
// anything under packages/users.
import { nextId } from "../../core/src/id.ts";
import { validateTitle } from "../../core/src/validate.ts";
import type { Task } from "./types.ts";

const tasksById = new Map<string, Task>();

/** Create and store a new task. Throws ValidationError on an empty title. */
export function createTask(title: string): Task {
  const cleanTitle = validateTitle(title);
  const task: Task = { id: nextId("tsk"), title: cleanTitle };
  tasksById.set(task.id, task);
  return task;
}

/** List all tasks created so far, in creation order. */
export function listTasks(): Task[] {
  return [...tasksById.values()];
}

/** Assign a task to a user, identified by id only (see module comment above). */
export function assignTask(taskId: string, assigneeUserId: string): Task {
  const task = tasksById.get(taskId);
  if (!task) {
    throw new Error(`task not found: ${taskId}`);
  }
  task.assigneeId = assigneeUserId;
  return task;
}

export type { Task };
