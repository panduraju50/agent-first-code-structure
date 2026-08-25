// Proves the enforcer actually enforces: constructs small synthetic graphs
// (no filesystem I/O) and asserts checkBoundaries() both passes clean input
// and fails each forbidden shape. Runs as part of `npm test` / `make test`.
import test from "node:test";
import assert from "node:assert/strict";
import { checkBoundaries } from "./lib/rules.mjs";

function file(overrides) {
  return {
    path: "src/x.ts",
    domain: "core",
    imports: [],
    capabilities: [],
    isClientFile: false,
    content: "",
    ...overrides,
  };
}

test("passes a clean, Design-D-compliant graph", () => {
  const files = [
    file({ path: "src/core/id/base62.ts", domain: "core", capabilities: ["core.id.base62"] }),
    file({
      path: "src/features/users/service.ts",
      domain: "users",
      imports: [{ specifier: "../../core", resolved: { path: "src/core/index.ts", domain: "core" } }],
    }),
    file({
      path: "src/composition/root.ts",
      domain: "composition",
      imports: [
        { specifier: "../features/users", resolved: { path: "src/features/users/index.ts", domain: "users" } },
        { specifier: "../features/tasks", resolved: { path: "src/features/tasks/index.ts", domain: "tasks" } },
      ],
    }),
  ];
  assert.deepEqual(checkBoundaries(files), []);
});

test("fails when a domain imports another domain directly (users -> tasks)", () => {
  const files = [
    file({
      path: "src/features/users/service.ts",
      domain: "users",
      imports: [{ specifier: "../tasks", resolved: { path: "src/features/tasks/index.ts", domain: "tasks" } }],
    }),
  ];
  const violations = checkBoundaries(files);
  assert.ok(violations.some((v) => v.rule === "domain-edge"));
});

test("fails when tasks imports users", () => {
  const files = [
    file({
      path: "src/features/tasks/service.ts",
      domain: "tasks",
      imports: [{ specifier: "../users", resolved: { path: "src/features/users/index.ts", domain: "users" } }],
    }),
  ];
  const violations = checkBoundaries(files);
  assert.ok(violations.some((v) => v.rule === "domain-edge"));
});

test("fails when a file outside core re-implements base62", () => {
  const files = [
    file({
      path: "src/features/tasks/leaky-id.ts",
      domain: "tasks",
      content: "export function toBase62(n) { return n.toString(62); }",
    }),
  ];
  const violations = checkBoundaries(files);
  assert.ok(violations.some((v) => v.rule === "duplicate-primitive"));
});

test("fails when the same capability is declared in two files", () => {
  const files = [
    file({ path: "src/core/id/base62.ts", capabilities: ["core.id.base62"] }),
    file({ path: "src/core/id/base62-copy.ts", capabilities: ["core.id.base62"] }),
  ];
  const violations = checkBoundaries(files);
  assert.ok(violations.some((v) => v.rule === "duplicate-capability"));
});

test("fails when a 'use client' file imports the composition root", () => {
  const files = [
    file({
      path: "src/app/tasks/TaskForm.tsx",
      domain: "app",
      isClientFile: true,
      imports: [
        { specifier: "../../composition/root", resolved: { path: "src/composition/root.ts", domain: "composition" } },
      ],
    }),
  ];
  const violations = checkBoundaries(files);
  assert.ok(violations.some((v) => v.rule === "client-server-boundary"));
});

test("allows a server (non-client) app file to import composition", () => {
  const files = [
    file({
      path: "src/app/tasks/page.tsx",
      domain: "app",
      isClientFile: false,
      imports: [
        { specifier: "../../composition/root", resolved: { path: "src/composition/root.ts", domain: "composition" } },
      ],
    }),
  ];
  assert.deepEqual(checkBoundaries(files), []);
});
