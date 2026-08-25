"use client";

// Client component. It imports `core` (pure, isomorphic — safe to ship to the
// browser) for local validation feedback, but MUST NOT import
// `../../composition/root` or any `features/*/repository` — those are
// server-only. scripts/check-boundaries.mjs enforces exactly this rule for
// every "use client" file.
import React, { useState } from "react";
import { validateTitle } from "../../core";

export interface TaskFormProps {
  onCreate: (title: string) => void;
}

export default function TaskForm({ onCreate }: TaskFormProps) {
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: { preventDefault: () => void }) {
    event.preventDefault();
    try {
      const clean = validateTitle(title);
      setError(null);
      onCreate(clean);
      setTitle("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={title}
        onChange={(event: { target: { value: string } }) => setTitle(event.target.value)}
        placeholder="New task title"
      />
      <button type="submit">Add task</button>
      {error ? <p role="alert">{error}</p> : null}
    </form>
  );
}
