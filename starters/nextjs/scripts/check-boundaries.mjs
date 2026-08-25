#!/usr/bin/env node
// The offline, stdlib-only boundary enforcer (Design D requirement 3's
// fallback to eslint-plugin-boundaries; see eslint.config.mjs for the
// idiomatic-tool version). Fails the build if:
//   (a) a domain imports another domain it isn't allowed to
//       (in particular: users <-> tasks), or
//   (b) any file outside src/core defines a base62 encoder or duplicates a
//       core validation primitive, or
//   (c) a "use client" file reaches into the server-only composition root.
//
// Zero dependencies beyond Node's standard library — runs with plain `node`.
import { loadSourceGraph } from "./lib/graph.mjs";
import { checkBoundaries } from "./lib/rules.mjs";

const files = loadSourceGraph();
const violations = checkBoundaries(files);

if (violations.length === 0) {
  console.log(`boundary check OK — ${files.length} files scanned, 0 violations`);
  process.exit(0);
}

console.error(`boundary check FAILED — ${violations.length} violation(s):\n`);
for (const v of violations) {
  console.error(`  [${v.rule}] ${v.message}`);
}
process.exit(1);
