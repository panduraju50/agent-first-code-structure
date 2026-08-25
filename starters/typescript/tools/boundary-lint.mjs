#!/usr/bin/env node
// Boundary enforcer for Design D. Node stdlib only — no node_modules
// required, so it runs in CI even when `npm install` is unavailable.
//
// Fails (exit 1) if:
//   (a) a domain package (anything under packages/ that isn't "core" or
//       "app") imports from another domain package. Only the composition
//       root ("app") is allowed to import across domains.
//   (b) any file outside packages/core defines a base62 encoder, or a
//       top-level declaration whose name shadows one of core's exported
//       primitives (e.g. a second `validateEmail`). Core is the one home
//       for these concerns; everything else must import them.
//
// This is the offline-guaranteed complement to .dependency-cruiser.js,
// which expresses the same two rules using the idiomatic dependency-graph
// linter but needs `npm install` to run.
import {
  listPackages,
  listSourceFiles,
  packageOf,
  parseImportSpecifiers,
  parseAllDeclarations,
  parseExportedDeclarations,
  resolveRelativeImport,
  readFile,
  toRepoRelative,
  PACKAGES_ROOT,
} from "./lib/scan.mjs";
import path from "node:path";

const CORE = "core";
const ROOT_EXEMPT = new Set(["app"]);
const packages = listPackages();
const domains = packages.filter((p) => p !== CORE && !ROOT_EXEMPT.has(p));

const files = listSourceFiles();
const violations = [];

// ---- Rule (a): domain independence -----------------------------------
for (const file of files) {
  const ownPackage = packageOf(file);
  if (ownPackage === null) continue;
  const isDomain = domains.includes(ownPackage);
  const isCore = ownPackage === CORE;
  if (!isDomain && !isCore) continue; // app is exempt from this rule

  const source = readFile(file);
  for (const specifier of parseImportSpecifiers(source)) {
    const resolved = resolveRelativeImport(file, specifier);
    if (resolved === null) continue; // bare import, e.g. "node:test"
    const targetPackage = packageOf(resolved);
    if (targetPackage === null || targetPackage === ownPackage) continue;

    if (isDomain && domains.includes(targetPackage)) {
      violations.push({
        rule: "no-domain-to-domain",
        file: toRepoRelative(file),
        detail: `imports "${specifier}" -> package "${targetPackage}". Domains may depend on core only; only packages/app may cross domains.`,
      });
    }
    if (isCore && targetPackage !== CORE) {
      violations.push({
        rule: "core-must-not-depend-on-domains",
        file: toRepoRelative(file),
        detail: `imports "${specifier}" -> package "${targetPackage}". packages/core must not depend on any domain or on app.`,
      });
    }
  }
}

// ---- Rule (b): no duplicate primitives outside core -------------------
const coreSrcDir = path.join(PACKAGES_ROOT, CORE, "src");
const corePrimitiveNames = new Set();
for (const file of files) {
  if (!file.startsWith(coreSrcDir)) continue;
  for (const decl of parseExportedDeclarations(readFile(file))) {
    corePrimitiveNames.add(decl.name);
  }
}

const BASE62_PATTERN = /base62/i;

for (const file of files) {
  const ownPackage = packageOf(file);
  if (ownPackage === CORE) continue; // core is the allowed home

  const source = readFile(file);
  for (const decl of parseAllDeclarations(source)) {
    if (BASE62_PATTERN.test(decl.name)) {
      violations.push({
        rule: "no-duplicate-base62-outside-core",
        file: toRepoRelative(file),
        detail: `declares "${decl.name}" — base62 encoding has exactly one home: packages/core/src/id.ts.`,
      });
      continue;
    }
    if (corePrimitiveNames.has(decl.name)) {
      violations.push({
        rule: "no-duplicate-primitive",
        file: toRepoRelative(file),
        detail: `declares "${decl.name}", which shadows the primitive exported by packages/core/src. Import it from core instead of re-implementing it.`,
      });
    }
  }
}

// ---- Report -------------------------------------------------------------
if (violations.length > 0) {
  console.error(`boundary-lint: ${violations.length} violation(s) found\n`);
  for (const v of violations) {
    console.error(`  [${v.rule}] ${v.file}\n      ${v.detail}\n`);
  }
  process.exit(1);
}

console.log(
  `boundary-lint: OK — checked ${files.length} file(s) across ${packages.length} package(s) (domains: ${domains.join(", ")}). No cross-domain imports, no duplicate primitives outside core.`,
);
