// The ONE place that walks src/ and parses the real module graph (imports +
// `// @capability` markers). Both scripts/check-boundaries.mjs and
// scripts/generate-manifest.mjs build on this — so the boundary rules and the
// generated manifest are always derived from the same facts about the same
// files, never hand-typed twice.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(fileURLToPath(import.meta.url), "../../..");
export const SRC_DIR = path.join(ROOT, "src");

const SOURCE_EXTENSIONS = [".ts", ".tsx"];
const SKIP_DIRS = new Set(["node_modules", "dist", ".next"]);

function toPosix(p) {
  return p.split(path.sep).join("/");
}

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walk(full);
    } else if (SOURCE_EXTENSIONS.includes(path.extname(entry.name))) {
      yield full;
    }
  }
}

/** Classify a repo-relative path (posix separators, e.g. "src/core/index.ts") into a Design D domain. */
export function domainOf(relPath) {
  if (relPath.startsWith("src/core/")) return "core";
  if (relPath.startsWith("src/features/users/")) return "users";
  if (relPath.startsWith("src/features/tasks/")) return "tasks";
  if (relPath.startsWith("src/composition/")) return "composition";
  if (relPath.startsWith("src/app/")) return "app";
  if (relPath.startsWith("src/types/")) return "types";
  return "other";
}

const IMPORT_LINE_RE =
  /^\s*(?:import|export)\s+(?:type\s+)?[^'"]*from\s+['"]([^'"]+)['"]|^\s*import\s+['"]([^'"]+)['"]/;
const DYNAMIC_IMPORT_RE = /\bimport\(\s*['"]([^'"]+)['"]\s*\)/g;
const CAPABILITY_RE = /^\s*\/\/\s*@capability\s+([\w.-]+)\s*$/;

function extractImportSpecifiers(content) {
  const specs = [];
  for (const line of content.split("\n")) {
    const m = IMPORT_LINE_RE.exec(line);
    if (m) specs.push(m[1] ?? m[2]);
  }
  let dm;
  DYNAMIC_IMPORT_RE.lastIndex = 0;
  while ((dm = DYNAMIC_IMPORT_RE.exec(content))) {
    specs.push(dm[1]);
  }
  return specs;
}

function extractCapabilities(content) {
  const caps = [];
  for (const line of content.split("\n")) {
    const m = CAPABILITY_RE.exec(line);
    if (m) caps.push(m[1]);
  }
  return caps;
}

/** True if the file's first meaningful line is the "use client" directive. */
function detectClientFile(content) {
  for (const raw of content.split("\n")) {
    const line = raw.trim();
    if (line === "" || line.startsWith("//") || line.startsWith("/*")) continue;
    return line === "'use client';" || line === '"use client";' || line === "'use client'" || line === '"use client"';
  }
  return false;
}

function resolveSpecifier(fromAbsFile, spec) {
  if (!spec.startsWith(".")) return null; // bare/external specifier (react, node:*, etc.) — not part of the local graph
  const base = path.resolve(path.dirname(fromAbsFile), spec);
  const candidates = [
    base,
    `${base}.ts`,
    `${base}.tsx`,
    path.join(base, "index.ts"),
    path.join(base, "index.tsx"),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      const rel = toPosix(path.relative(ROOT, candidate));
      return { path: rel, domain: domainOf(rel) };
    }
  }
  return null; // unresolved local import (typo, or resolves outside src) — reported as-is, not silently dropped
}

/**
 * Load the full source graph: one record per file under src/, each with its
 * domain, parsed imports (resolved to a domain when local), declared
 * capabilities, and whether it's a "use client" file.
 */
export function loadSourceGraph() {
  const files = [];
  for (const absFile of walk(SRC_DIR)) {
    const relPath = toPosix(path.relative(ROOT, absFile));
    const content = fs.readFileSync(absFile, "utf8");
    const imports = extractImportSpecifiers(content).map((specifier) => ({
      specifier,
      resolved: resolveSpecifier(absFile, specifier),
    }));
    files.push({
      path: relPath,
      domain: domainOf(relPath),
      imports,
      capabilities: extractCapabilities(content),
      isClientFile: detectClientFile(content),
      content,
    });
  }
  files.sort((a, b) => a.path.localeCompare(b.path));
  return files;
}
