// The `tasks` domain depends on `core` only — never on `users`. Note that
// `assignTask` takes a bare `assigneeId: string`, not a `User`: this domain
// has no way to even express a dependency on `users`.
import { nextId, validateTitle } from "../../core";
import type { Task } from "./types";
import { saveTask, findTask, allTasks } from "./repository";

// @capability tasks.create
export function createTask(input: { title: string }): Task {
  const title = validateTitle(input.title);
  const task: Task = { id: nextId("tsk"), title, status: "open", assigneeId: null };
  return saveTask(task);
}

// @capability tasks.list
export function listTasks(): Task[] {
  return allTasks();
}

// @capability tasks.assign
export function assignTask(taskId: string, assigneeId: string): Task {
  const task = findTask(taskId);
  if (!task) {
    throw new Error(`task not found: ${taskId}`);
  }
  const updated: Task = { ...task, status: "assigned", assigneeId };
  return saveTask(updated);
}
