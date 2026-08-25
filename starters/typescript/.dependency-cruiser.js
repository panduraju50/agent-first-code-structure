/**
 * Idiomatic dependency-graph enforcement for Design D, using
 * dependency-cruiser (https://github.com/sverweij/dependency-cruiser).
 *
 * This expresses the SAME two rules as tools/boundary-lint.mjs:
 *   1. Domains (users, tasks) may depend on core, never on each other.
 *      Only packages/app may import across domains.
 *   2. Nothing outside packages/core may re-implement a base62 encoder.
 *
 * Requires `npm install` (devDependency: dependency-cruiser), which this
 * sandbox cannot run offline — so CI runs both this AND
 * tools/boundary-lint.mjs: this is the idiomatic, industry-standard tool;
 * boundary-lint.mjs is the offline-guaranteed fallback that needs no
 * node_modules. See README.md, "The boundary enforcer, twice".
 *
 * Run locally with: npx depcruise packages --config .dependency-cruiser.js
 *
 * @type {import('dependency-cruiser').IConfiguration}
 */
module.exports = {
  forbidden: [
    {
      name: "no-users-importing-tasks",
      comment:
        "packages/users may depend on packages/core, but never on packages/tasks. Only packages/app may cross domains.",
      severity: "error",
      from: { path: "^packages/users" },
      to: { path: "^packages/tasks" },
    },
    {
      name: "no-tasks-importing-users",
      comment:
        "packages/tasks may depend on packages/core, but never on packages/users. Only packages/app may cross domains.",
      severity: "error",
      from: { path: "^packages/tasks" },
      to: { path: "^packages/users" },
    },
    {
      name: "core-must-not-depend-on-domains-or-app",
      comment: "packages/core is the dependency-free foundation: nothing above it may be imported back into it.",
      severity: "error",
      from: { path: "^packages/core" },
      to: { path: "^packages/(users|tasks|app)" },
    },
    {
      name: "no-duplicate-base62-outside-core",
      comment: "Base62 id encoding has exactly one home: packages/core/src/id.ts.",
      severity: "error",
      from: { pathNot: "^packages/core" },
      to: { path: "base62", pathNot: "^packages/core" },
    },
  ],
  options: {
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: {
      extensions: [".ts", ".js"],
    },
    exclude: {
      path: "(^|/)(dist|node_modules)(/|$)",
    },
  },
};
