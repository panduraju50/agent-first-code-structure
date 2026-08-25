#!/usr/bin/env node
// The full offline CI pipeline: build + test, boundary-lint, manifest-drift
// check. Mirrors .github/workflows/ci.yml and the Makefile's `ci` target —
// all three run these same four steps.
import { spawnSync } from "node:child_process";
import { ROOT } from "./lib/graph.mjs";

const steps = [
  { name: "build + test", cmd: "node", args: ["scripts/build-and-test.mjs"] },
  { name: "boundary lint (stdlib fallback)", cmd: "node", args: ["scripts/check-boundaries.mjs"] },
  { name: "manifest drift check", cmd: "node", args: ["scripts/generate-manifest.mjs", "--check"] },
];

let failed = false;
for (const step of steps) {
  console.log(`\n=== ${step.name} ===`);
  const result = spawnSync(step.cmd, step.args, { cwd: ROOT, stdio: "inherit" });
  if (result.status !== 0) {
    failed = true;
    console.error(`\n✗ ${step.name} failed`);
  } else {
    console.log(`\n✓ ${step.name} passed`);
  }
}

process.exit(failed ? 1 : 0);
