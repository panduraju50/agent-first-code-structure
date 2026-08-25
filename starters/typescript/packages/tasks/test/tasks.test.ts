import { test } from "node:test";
import assert from "node:assert/strict";
import { createTask, listTasks, assignTask } from "../src/index.ts";
import { ValidationError } from "../../core/src/validate.ts";

test("createTask stores a retrievable task with a base62 id", () => {
  const before = listTasks().length;
  const task = createTask("Ship it");
  assert.match(task.id, /^tsk_[0-9A-Za-z]+$/);
  assert.equal(listTasks().length, before + 1);
});

test("createTask rejects an empty title via core's validator", () => {
  assert.throws(() => createTask("   "), ValidationError);
});

test("assignTask attaches an assignee id by reference only (no users import)", () => {
  const task = createTask("Review PR");
  const updated = assignTask(task.id, "usr_someExternalId");
  assert.equal(updated.assigneeId, "usr_someExternalId");
});

test("assignTask throws for an unknown task id", () => {
  assert.throws(() => assignTask("tsk_doesNotExist", "usr_x"), /task not found/);
});
