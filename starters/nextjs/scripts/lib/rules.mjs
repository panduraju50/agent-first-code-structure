// The Design D boundary rules, as pure data + a pure function over an
// already-parsed file graph (see lib/graph.mjs). Kept dependency-free and
// side-effect-free so scripts/check-boundaries.test.mjs can exercise it
// directly with synthetic fixtures, without touching the filesystem.
//
// This table mirrors eslint.config.mjs's `boundaries/element-types` rule
// exactly — the stdlib checker (this file) and the idiomatic ESLint plugin
// enforce the SAME typed edges, so a domain that "should not" depend on
// another fails identically whichever tool runs it.
export const ALLOWED_EDGES = {
  core: new Set(["core"]),
  users: new Set(["core", "users"]),
  tasks: new Set(["core", "tasks"]),
  composition: new Set(["core", "users", "tasks", "composition"]),
  app: new Set(["core", "composition", "app"]),
  types: new Set(["types"]),
};

// Patterns that indicate a cross-cutting primitive is being re-implemented
// somewhere other than its one home in `core`.
// Deliberately code-shaped (declarations/definitions), not just the bare
// word — a test description like `"assigns a base62 id"` must not trip this.
const FORBIDDEN_PRIMITIVE_PATTERNS = [
  { id: "base62-encoder", pattern: /\b(?:function|const|let)\s+\w*[Bb]ase62\w*\s*[(=]/ },
  { id: "base62-alphabet", pattern: /0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/ },
  { id: "email-validator", pattern: /function\s+validateEmail\b/ },
  { id: "title-validator", pattern: /function\s+validateTitle\b/ },
];

/**
 * @param {Array<{path:string, domain:string, imports:Array<{specifier:string, resolved:{path:string,domain:string}|null}>, capabilities:string[], isClientFile:boolean, content:string}>} files
 * @returns {Array<{rule:string, file:string, message:string}>}
 */
export function checkBoundaries(files) {
  const violations = [];

  for (const file of files) {
    for (const imp of file.imports) {
      if (!imp.resolved) continue; // external/bare specifier (react, node:*, ...) — not governed
      const targetDomain = imp.resolved.domain;
      if (targetDomain === file.domain) continue;

      const allowed = ALLOWED_EDGES[file.domain];
      if (!allowed || !allowed.has(targetDomain)) {
        violations.push({
          rule: "domain-edge",
          file: file.path,
          message: `${file.domain} -> ${targetDomain} is not an allowed edge (import "${imp.specifier}" in ${file.path} -> ${imp.resolved.path})`,
        });
        continue;
      }

      // Client/server boundary: a "use client" file may use core (pure,
      // isomorphic) but must never reach into the server-only composition
      // root, even though `app -> composition` is otherwise allowed.
      if (file.isClientFile && targetDomain === "composition") {
        violations.push({
          rule: "client-server-boundary",
          file: file.path,
          message: `"use client" file ${file.path} imports server-only composition module "${imp.specifier}"`,
        });
      }
    }

    if (file.domain !== "core") {
      for (const { id, pattern } of FORBIDDEN_PRIMITIVE_PATTERNS) {
        if (pattern.test(file.content)) {
          violations.push({
            rule: "duplicate-primitive",
            file: file.path,
            message: `${file.path} appears to define a "${id}" primitive; that has exactly one home, in src/core`,
          });
        }
      }
    }
  }

  const owners = new Map();
  for (const file of files) {
    for (const capability of file.capabilities) {
      const list = owners.get(capability) ?? [];
      list.push(file.path);
      owners.set(capability, list);
    }
  }
  for (const [capability, ownerFiles] of owners) {
    if (ownerFiles.length > 1) {
      violations.push({
        rule: "duplicate-capability",
        file: ownerFiles.join(", "),
        message: `capability "${capability}" is declared in more than one file: ${ownerFiles.join(", ")}`,
      });
    }
  }

  return violations;
}
