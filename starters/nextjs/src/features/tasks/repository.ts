// In-memory persistence for the `tasks` domain. Server-only, same rule as
// features/users/repository.ts.
import type { Task } from "./types";

const tasks = new Map<string, Task>();

export function saveTask(task: Task): Task {
  tasks.set(task.id, task);
  return task;
}

export function findTask(id: string): Task | undefined {
  return tasks.get(id);
}

export function allTasks(): Task[] {
  return Array.from(tasks.values());
}
