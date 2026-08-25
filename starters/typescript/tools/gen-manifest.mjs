#!/usr/bin/env node
// Generates manifest.json — a capability-to-owning-file map plus the
// package/file dependency edges — directly from the real module graph
// under packages/. Nothing here is hand-authored: run with --write to
// regenerate it, or --check to verify the committed file still matches
// the graph (used as CI's drift check).
//
// Output is fully deterministic (sorted, no timestamps) so that
// `--write` twice in a row with no code changes produces a byte-identical
// file, and `--check` only ever fails when the graph actually changed.
import { writeFileSync, readFileSync, existsSync } from "node:fs";
import path from "node:path";
import {
  listPackages,
  listSourceFiles,
  packageOf,
  parseImportSpecifiers,
  parseExportedDeclarations,
  resolveRelativeImport,
  readFile,
  toRepoRelative,
  REPO_ROOT,
  PACKAGES_ROOT,
} from "./lib/scan.mjs";

const MANIFEST_PATH = path.join(REPO_ROOT, "manifest.json");

function buildManifest() {
  const packages = listPackages();
  const files = listSourceFiles();

  // capabilities: every exported top-level declaration under packages/*/src
  // (test files export test setup, not product capabilities, so they're
  // excluded here but still counted in the edges below).
  const capabilities = [];
  for (const file of files) {
    const pkg = packageOf(file);
    const isSrc = toRepoRelative(file).split("/").includes("src");
    if (!isSrc) continue;
    for (const decl of parseExportedDeclarations(readFile(file))) {
      capabilities.push({
        capability: decl.name,
        kind: decl.kind,
        package: pkg,
        file: toRepoRelative(file),
      });
    }
  }
  capabilities.sort((a, b) => (a.capability + a.file).localeCompare(b.capability + b.file));

  // fileEdges / packageEdges: every relative import between two files
  // under packages/, resolved from the real source text.
  const fileEdgeSet = new Set();
  const fileEdges = [];
  const packageEdgeSet = new Set();
  const packageEdges = [];

  for (const file of files) {
    const fromPkg = packageOf(file);
    const source = readFile(file);
    for (const specifier of parseImportSpecifiers(source)) {
      const resolved = resolveRelativeImport(file, specifier);
      if (resolved === null) continue;
      const toPkg = packageOf(resolved);
      if (toPkg === null) continue;

      const fileKey = `${toRepoRelative(file)} -> ${toRepoRelative(resolved)}`;
      if (!fileEdgeSet.has(fileKey)) {
        fileEdgeSet.add(fileKey);
        fileEdges.push({ from: toRepoRelative(file), to: toRepoRelative(resolved) });
      }

      if (fromPkg !== toPkg) {
        const pkgKey = `${fromPkg} -> ${toPkg}`;
        if (!packageEdgeSet.has(pkgKey)) {
          packageEdgeSet.add(pkgKey);
          packageEdges.push({ from: fromPkg, to: toPkg });
        }
      }
    }
  }

  fileEdges.sort((a, b) => (a.from + a.to).localeCompare(b.from + b.to));
  packageEdges.sort((a, b) => (a.from + a.to).localeCompare(b.from + b.to));

  const manifest = {
    generatedBy: "tools/gen-manifest.mjs",
    note: "Generated from the packages/ module graph. Do not hand-edit — run `npm run generate:manifest`.",
    packages,
    capabilities,
    packageEdges,
    fileEdges,
  };

  return JSON.stringify(manifest, null, 2) + "\n";
}

function main() {
  const mode = process.argv[2];
  const generated = buildManifest();

  if (mode === "--write") {
    writeFileSync(MANIFEST_PATH, generated, "utf8");
    console.log(`gen-manifest: wrote ${toRepoRelative(MANIFEST_PATH)}`);
    return;
  }

  if (mode === "--check") {
    if (!existsSync(MANIFEST_PATH)) {
      console.error(
        `gen-manifest: ${toRepoRelative(MANIFEST_PATH)} does not exist. Run \`npm run generate:manifest\`.`,
      );
      process.exit(1);
    }
    const committed = readFileSync(MANIFEST_PATH, "utf8");
    if (committed !== generated) {
      console.error(
        "gen-manifest: manifest.json is out of date with packages/ — code changed but the manifest was not regenerated.\n" +
          "Run `npm run generate:manifest` and commit the result.",
      );
      process.exit(1);
    }
    console.log("gen-manifest: manifest.json matches the current module graph (no drift).");
    return;
  }

  console.error("usage: node tools/gen-manifest.mjs --write | --check");
  process.exit(2);
}

main();
