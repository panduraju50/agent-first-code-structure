#!/usr/bin/env node
// Offline build + test: `tsc` compiles src/ to plain CommonJS (see
// tsconfig.build.json), then Node's built-in test runner runs every
// *.test.js under dist/ plus the enforcer's own self-tests under scripts/.
import { spawnSync } from "node:child_process";
import { ROOT } from "./lib/graph.mjs";

function run(cmd, args) {
  console.log(`\n$ ${cmd} ${args.join(" ")}`);
  const result = spawnSync(cmd, args, { cwd: ROOT, stdio: "inherit" });
  if (result.error) {
    console.error(`failed to run "${cmd}": ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run("tsc", ["-p", "tsconfig.build.json"]);
// Bare directory args make Node's CJS loader try to `require()` the
// directory itself in some Node versions; explicit globs are unambiguous.
run("node", ["--test", "dist/**/*.test.js", "scripts/**/*.test.mjs"]);
