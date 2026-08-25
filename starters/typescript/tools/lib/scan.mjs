// Shared, dependency-free (Node stdlib only) helpers for scanning the
// packages/ source tree. Used by both tools/boundary-lint.mjs and
// tools/gen-manifest.mjs so the two enforcement/generation scripts agree
// on exactly what counts as "a file", "an import", and "a declaration".
//
// This is a regex-based scanner, not a real TypeScript parser. That is a
// deliberate, documented trade-off for a small starter repo running with
// zero installed dependencies (see README.md "Why regex, not a real
// parser"): it is precise enough for straightforward, idiomatic TS import
// syntax, and the CI-time complement is the real tool, dependency-cruiser,
// configured in .dependency-cruiser.js.

import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

export const REPO_ROOT = path.resolve(import.meta.dirname, "..", "..");
export const PACKAGES_ROOT = path.join(REPO_ROOT, "packages");

/** All package directory names under packages/, e.g. ["app","core","tasks","users"]. */
export function listPackages() {
  return readdirSync(PACKAGES_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

/** Recursively collect every .ts file under a directory (skips node_modules/dist). */
function walk(dir, out) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, out);
    } else if (entry.isFile() && entry.name.endsWith(".ts")) {
      out.push(full);
    }
  }
  return out;
}

/**
 * All .ts source files under packages/&lt;name&gt;/src and packages/&lt;name&gt;/test,
 * as absolute paths, sorted deterministically.
 */
export function listSourceFiles() {
  const files = [];
  for (const pkg of listPackages()) {
    for (const sub of ["src", "test"]) {
      const dir = path.join(PACKAGES_ROOT, pkg, sub);
      try {
        if (statSync(dir).isDirectory()) walk(dir, files);
      } catch {
        // no test/ (or src/) directory for this package — fine, skip it
      }
    }
  }
  return files.sort();
}

/** The packages/&lt;name&gt; this absolute file path belongs to, or null if outside packages/. */
export function packageOf(absFilePath) {
  const rel = path.relative(PACKAGES_ROOT, absFilePath);
  if (rel.startsWith("..")) return null;
  return rel.split(path.sep)[0];
}

// Matches: import ... from '...'; export ... from '...'; bare import '...';
// and dynamic import('...'). Deliberately simple — see module doc comment.
const IMPORT_RE =
  /(?:import|export)\s+(?:[\s\S]*?\bfrom\s+)?["']([^"']+)["']|import\s*\(\s*["']([^"']+)["']\s*\)/g;

/** Extract every static/dynamic import specifier string that appears in TS source. */
export function parseImportSpecifiers(source) {
  const specifiers = [];
  for (const match of source.matchAll(IMPORT_RE)) {
    specifiers.push(match[1] ?? match[2]);
  }
  return specifiers;
}

/**
 * Resolve a relative import specifier (e.g. "../../core/src/id.ts") from a
 * given file to an absolute path. Returns null for non-relative specifiers
 * (bare/package imports like "node:test").
 */
export function resolveRelativeImport(fromFile, specifier) {
  if (!specifier.startsWith(".")) return null;
  return path.normalize(path.join(path.dirname(fromFile), specifier));
}

// Matches top-level `export function name`, `export const name =`,
// `export class name`, `export interface name`, `export type name`.
const EXPORTED_DECL_RE =
  /^export\s+(?:async\s+)?(function|const|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)/gm;

// Matches ANY top-level declaration, exported or not — used by the
// duplicate-primitive check, since a non-exported lookalike helper is just
// as much a violation of "one home per concern" as an exported one.
const ANY_DECL_RE =
  /^(?:export\s+)?(?:async\s+)?(function|const|class|interface|type)\s+([A-Za-z_$][A-Za-z0-9_$]*)/gm;

export function parseExportedDeclarations(source) {
  return [...source.matchAll(EXPORTED_DECL_RE)].map(([, kind, name]) => ({ kind, name }));
}

export function parseAllDeclarations(source) {
  return [...source.matchAll(ANY_DECL_RE)].map(([, kind, name]) => ({ kind, name }));
}

export function readFile(absPath) {
  return readFileSync(absPath, "utf8");
}

/** Repo-relative, forward-slash path, for stable output across platforms. */
export function toRepoRelative(absPath) {
  return path.relative(REPO_ROOT, absPath).split(path.sep).join("/");
}
