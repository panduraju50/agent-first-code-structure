export type TaskStatus = "open" | "assigned" | "done";

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  // Deliberately an opaque string, not a `User` — `tasks` does not know the
  // `users` domain exists. Whether the id refers to a real user is validated
  // by the composition root, the one place both domains are visible.
  assigneeId: string | null;
}
