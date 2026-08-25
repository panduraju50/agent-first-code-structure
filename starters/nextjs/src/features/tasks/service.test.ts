import test from "node:test";
import assert from "node:assert/strict";
import { createTask, listTasks, assignTask } from "./service";

test("createTask trims the title and assigns a base62 id", () => {
  const task = createTask({ title: "  Ship the feature  " });
  assert.equal(task.title, "Ship the feature");
  assert.match(task.id, /^tsk_[0-9A-Za-z]+$/);
  assert.equal(task.status, "open");
  assert.equal(task.assigneeId, null);
});

test("createTask rejects an empty title", () => {
  assert.throws(() => createTask({ title: "   " }), /title must not be empty/);
});

test("assignTask moves a task to assigned and records the (opaque) assignee id", () => {
  const task = createTask({ title: "Review PR" });
  const assigned = assignTask(task.id, "usr_someone");
  assert.equal(assigned.status, "assigned");
  assert.equal(assigned.assigneeId, "usr_someone");
  assert.ok(listTasks().some((t) => t.id === task.id));
});

test("assignTask throws for an unknown task id", () => {
  assert.throws(() => assignTask("tsk_doesnotexist", "usr_x"), /task not found/);
});
