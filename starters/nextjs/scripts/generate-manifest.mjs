#!/usr/bin/env node
// Generates MANIFEST.generated.json from the REAL module graph — it is never
// hand-authored. Capabilities come from `// @capability` markers found while
// walking src/; dependency edges come from parsing actual import statements.
// Run `node scripts/generate-manifest.mjs --check` (wired into CI) to fail
// when the committed manifest has drifted from the source it describes.
import fs from "node:fs";
import path from "node:path";
import { ROOT, loadSourceGraph } from "./lib/graph.mjs";

const OUT_PATH = path.join(ROOT, "MANIFEST.generated.json");

function sortEntries(obj) {
  return Object.fromEntries(Object.entries(obj).sort(([a], [b]) => a.localeCompare(b)));
}

function buildManifest() {
  const files = loadSourceGraph();

  const capabilities = {};
  for (const f of files) {
    for (const cap of f.capabilities) {
      // Last write wins if a capability were ever (wrongly) declared twice;
      // scripts/check-boundaries.mjs is what actually fails the build for
      // that case (rule: duplicate-capability) — the manifest just reflects
      // the graph as found.
      capabilities[cap] = f.path;
    }
  }

  const fileEdges = new Set();
  const domainEdges = new Set();
  for (const f of files) {
    for (const imp of f.imports) {
      if (!imp.resolved) continue;
      fileEdges.add(`${f.path} -> ${imp.resolved.path}`);
      if (imp.resolved.domain !== f.domain) {
        domainEdges.add(`${f.domain} -> ${imp.resolved.domain}`);
      }
    }
  }

  const byDomain = (domain) => files.filter((f) => f.domain === domain).map((f) => f.path).sort();

  return {
    capabilities: sortEntries(capabilities),
    domains: {
      core: byDomain("core"),
      users: byDomain("users"),
      tasks: byDomain("tasks"),
      composition: byDomain("composition"),
      app: byDomain("app"),
    },
    edges: {
      files: [...fileEdges].sort(),
      domains: [...domainEdges].sort(),
    },
  };
}

function serialize(manifest) {
  return `${JSON.stringify(manifest, null, 2)}\n`;
}

const manifest = serialize(buildManifest());
const checkMode = process.argv.includes("--check");

if (checkMode) {
  const existing = fs.existsSync(OUT_PATH) ? fs.readFileSync(OUT_PATH, "utf8") : null;
  if (existing !== manifest) {
    console.error("MANIFEST.generated.json is stale relative to src/.");
    console.error('Run "node scripts/generate-manifest.mjs" (or `npm run manifest:generate`) and commit the result.');
    process.exit(1);
  }
  console.log("MANIFEST.generated.json is up to date.");
  process.exit(0);
}

fs.writeFileSync(OUT_PATH, manifest);
console.log(`wrote ${path.relative(ROOT, OUT_PATH)}`);
