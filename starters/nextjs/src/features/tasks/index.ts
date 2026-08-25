// Public barrel for the `tasks` domain — the only surface the composition
// root (or anything else) is allowed to import from.
export type { Task, TaskStatus } from "./types";
export { createTask, listTasks, assignTask } from "./service";
