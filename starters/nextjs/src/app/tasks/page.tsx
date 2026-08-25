// Server component. Note this imports `../../composition/root`, NOT
// `../../features/tasks` or `../../features/users` directly — `app` only ever
// talks to the composition root, which is the sole place both domains are
// wired together.
import React from "react";
import { runScenario } from "../../composition/root";
import TaskForm from "./TaskForm";

export default function TasksPage() {
  const scenario = runScenario();

  return (
    <main>
      <h1>Tasks</h1>
      <ul>
        {scenario.tasks.map((task) => (
          <li key={task.id}>
            {task.title} — {task.status}
            {task.assigneeId ? ` (assigned to ${scenario.user.name})` : ""}
          </li>
        ))}
      </ul>
      {/* In a real deployment this would submit through a Server Action
          exposed by the composition root. Wiring that up needs the real
          Next.js runtime, so here TaskForm only demonstrates the client
          boundary: it validates input locally using core (pure, safe to run
          in the browser) and never touches server-only state itself. */}
      <TaskForm onCreate={() => undefined} />
    </main>
  );
}
