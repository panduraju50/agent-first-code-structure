//! xtask -- the Design D tooling for this workspace.
//!
//! Two jobs, both driven off the *real* module graph rather than anything
//! hand-authored:
//!
//! 1. `boundary-lint`  -- the boundary enforcer (rule 3). Reads every
//!    crate's `Cargo.toml` and fails if a domain crate depends on another
//!    domain crate, or if a domain crate's workspace deps are anything
//!    other than exactly `{corelib}`. Also greps every non-core crate's
//!    source for base62-shaped code, and fails if it finds any -- there
//!    must be exactly one base62 implementation, and it must live in
//!    `crates/core`.
//!
//! 2. `manifest-gen` / `manifest-check` -- the manifest (rule 4). Walks
//!    every crate's source for `/// capability: <name>` doc comments and
//!    combines that with the dependency edges read from `Cargo.toml` to
//!    produce `MANIFEST.md`. `manifest-check` regenerates the same content
//!    in memory and fails if it differs from what is committed, which is
//!    the drift check: if you change code (adding/removing a capability,
//!    or changing a dependency) without regenerating the manifest, CI
//!    fails.
//!
//! No external crates: this file uses only `std`. The little TOML reader
//! below is intentionally not a general-purpose parser -- it understands
//! exactly the shape of the `Cargo.toml` files in this workspace (a
//! `[dependencies]` table of `name = "..."` / `name = { path = "..." }`
//! lines), which is all a real dependency-graph check over our own
//! manifests needs.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::exit;

const ALL_CRATES: &[&str] = &["core", "users", "tasks", "app"];
const DOMAINS: &[&str] = &["users", "tasks"];
const CORE_PACKAGE: &str = "corelib";

fn workspace_root() -> PathBuf {
    // xtask/Cargo.toml lives at <root>/xtask/Cargo.toml, so the workspace
    // root is always this crate's parent directory -- independent of
    // whatever the caller's current directory happens to be.
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("xtask has a parent directory")
        .to_path_buf()
}

fn crate_dir(root: &Path, crate_name: &str) -> PathBuf {
    root.join("crates").join(crate_name)
}

/// Returns the workspace-local dependency names declared under
/// `[dependencies]` in `cargo_toml` -- i.e. every entry whose value
/// contains `path`. Non-path (crates.io / version-only) dependencies are
/// ignored, though this workspace has none.
fn local_path_deps(cargo_toml: &Path) -> Vec<String> {
    let text = fs::read_to_string(cargo_toml)
        .unwrap_or_else(|e| panic!("reading {}: {e}", cargo_toml.display()));

    let mut in_dependencies = false;
    let mut deps = Vec::new();
    for raw_line in text.lines() {
        let line = raw_line.trim();
        if let Some(section) = line.strip_prefix('[') {
            in_dependencies = section.trim_end_matches(']') == "dependencies";
            continue;
        }
        if !in_dependencies || line.is_empty() || line.starts_with('#') {
            continue;
        }
        let parts: Vec<&str> = line.splitn(2, '=').collect();
        if parts.len() != 2 {
            continue;
        }
        let name = parts[0].trim().trim_matches('"').to_string();
        let value = parts[1];
        if value.contains("path") {
            deps.push(name);
        }
    }
    deps
}

fn find_rs_files(dir: &Path, out: &mut Vec<PathBuf>) {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            find_rs_files(&path, out);
        } else if path.extension().and_then(|e| e.to_str()) == Some("rs") {
            out.push(path);
        }
    }
}

/// Heuristic markers for "this looks like a base62 implementation". Tuned
/// against the real implementation in crates/core/src/base62.rs; grep-based
/// per the assignment ("clippy-based or grep-based rule").
fn base62_markers(text: &str) -> Vec<&'static str> {
    const MARKERS: &[&str] = &["base62", "Base62", "% 62", "62usize", "62u64", "ALPHABET"];
    MARKERS
        .iter()
        .copied()
        .filter(|m| text.contains(m))
        .collect()
}

fn boundary_lint(root: &Path) -> Result<(), Vec<String>> {
    let mut errors = Vec::new();

    // --- Rule 3a: no domain-to-domain edge; domain deps == {corelib}. ---
    for &domain in DOMAINS {
        let toml_path = crate_dir(root, domain).join("Cargo.toml");
        let deps: BTreeSet<String> = local_path_deps(&toml_path).into_iter().collect();

        for &other in DOMAINS {
            if other != domain && deps.contains(other) {
                errors.push(format!(
                    "boundary violation: crates/{domain}/Cargo.toml depends on crate '{other}' \
                     -- domain-to-domain edges are forbidden (both must depend on core only)"
                ));
            }
        }

        let expected: BTreeSet<String> = [CORE_PACKAGE.to_string()].into_iter().collect();
        if deps != expected {
            errors.push(format!(
                "boundary violation: crates/{domain}/Cargo.toml workspace deps are {deps:?}, \
                 expected exactly {{\"{CORE_PACKAGE}\"}}"
            ));
        }
    }

    // --- Rule 3b: core depends on nothing in the workspace. ---
    let core_toml = crate_dir(root, "core").join("Cargo.toml");
    let core_deps = local_path_deps(&core_toml);
    if !core_deps.is_empty() {
        errors.push(format!(
            "boundary violation: crates/core/Cargo.toml has workspace deps {core_deps:?}, \
             core must depend on nothing else in the workspace"
        ));
    }

    // --- Rule 3c: exactly one base62 implementation, and it lives in core.
    for &member in ALL_CRATES {
        if member == "core" {
            continue;
        }
        let src_dir = crate_dir(root, member).join("src");
        let mut files = Vec::new();
        find_rs_files(&src_dir, &mut files);
        for file in files {
            let text = fs::read_to_string(&file).unwrap_or_default();
            let hits = base62_markers(&text);
            if !hits.is_empty() {
                let rel = file.strip_prefix(root).unwrap_or(&file).display();
                errors.push(format!(
                    "duplicate-primitive violation: {rel} references base62 internals \
                     ({hits:?}) outside crates/core -- the encoder must live only in \
                     corelib::base62"
                ));
            }
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

#[derive(Debug, Clone)]
struct Capability {
    name: String,
    krate: String,
    file: String,
    line: usize,
    signature: String,
}

/// Scans every crate's `src/` for `/// capability: <name>` doc comments and
/// records the next non-doc-comment, non-attribute line as the item it
/// documents. This is the "generated from the real module graph" half of
/// the manifest.
fn extract_capabilities(root: &Path) -> Vec<Capability> {
    let mut caps = Vec::new();

    for &member in ALL_CRATES {
        let src_dir = crate_dir(root, member).join("src");
        let mut files = Vec::new();
        find_rs_files(&src_dir, &mut files);
        files.sort();

        for file in files {
            let text = fs::read_to_string(&file).unwrap_or_default();
            let lines: Vec<&str> = text.lines().collect();

            for (i, line) in lines.iter().enumerate() {
                let trimmed = line.trim();
                let Some(rest) = trimmed.strip_prefix("/// capability:") else {
                    continue;
                };
                let name = rest.trim().to_string();

                let mut j = i + 1;
                while j < lines.len() {
                    let t = lines[j].trim();
                    if t.is_empty() || t.starts_with("///") || t.starts_with("#[") {
                        j += 1;
                        continue;
                    }
                    break;
                }
                if j >= lines.len() {
                    continue;
                }

                let rel_file = file
                    .strip_prefix(root)
                    .unwrap_or(&file)
                    .to_string_lossy()
                    .replace('\\', "/");

                caps.push(Capability {
                    name,
                    krate: member.to_string(),
                    file: rel_file,
                    line: j + 1,
                    signature: lines[j].trim().to_string(),
                });
            }
        }
    }

    caps.sort_by(|a, b| (&a.name, &a.file, a.line).cmp(&(&b.name, &b.file, b.line)));
    caps
}

fn render_manifest(root: &Path) -> String {
    let caps = extract_capabilities(root);

    let mut edges: Vec<(String, String)> = Vec::new();
    for &member in ALL_CRATES {
        let toml_path = crate_dir(root, member).join("Cargo.toml");
        for dep in local_path_deps(&toml_path) {
            edges.push((member.to_string(), dep));
        }
    }
    edges.sort();

    let mut out = String::new();
    out.push_str("<!-- GENERATED FILE. Do not hand-edit. -->\n");
    out.push_str("<!-- Regenerate with: cargo run -p xtask --offline -- manifest-gen -->\n\n");
    out.push_str("# Capability & Dependency Manifest\n\n");
    out.push_str(
        "Derived automatically from the real module graph: capabilities come from \
         `/// capability: <name>` doc-comment markers found by walking each crate's \
         `src/`, and dependency edges come from parsing each crate's `Cargo.toml` \
         `[dependencies]` table. Nothing below is hand-typed; run `xtask manifest-gen` \
         to regenerate it and `xtask manifest-check` to verify it is not stale. See \
         README.md for how this maps onto Design D.\n\n",
    );

    out.push_str("## Capabilities (capability -> owning file)\n\n");
    out.push_str("| capability | crate | file | line | signature |\n");
    out.push_str("|---|---|---|---|---|\n");
    for c in &caps {
        out.push_str(&format!(
            "| {} | {} | {} | {} | `{}` |\n",
            c.name, c.krate, c.file, c.line, c.signature
        ));
    }

    out.push_str("\n## Dependency edges (workspace-local)\n\n");
    out.push_str("| from crate | depends on |\n");
    out.push_str("|---|---|\n");
    for (from, to) in &edges {
        out.push_str(&format!("| {from} | {to} |\n"));
    }

    out.push_str(
        "\n_This table is the enforced graph: `users -> corelib`, `tasks -> corelib`, \
         `app -> corelib, users, tasks`, `core -> (nothing)`. `xtask boundary-lint` fails \
         the build the moment a `users <-> tasks` edge appears, or a second base62 \
         implementation shows up outside `crates/core`._\n",
    );

    out
}

fn main() {
    let root = workspace_root();
    let cmd = std::env::args().nth(1).unwrap_or_default();

    match cmd.as_str() {
        "boundary-lint" => match boundary_lint(&root) {
            Ok(()) => {
                println!(
                    "boundary-lint: OK -- no domain-to-domain edges, domain deps == {{corelib}} \
                     only, no duplicate base62 implementation found"
                );
            }
            Err(errors) => {
                for e in &errors {
                    eprintln!("ERROR: {e}");
                }
                eprintln!("boundary-lint: FAILED ({} violation(s))", errors.len());
                exit(1);
            }
        },
        "manifest-gen" => {
            let content = render_manifest(&root);
            let out_path = root.join("MANIFEST.md");
            fs::write(&out_path, content).expect("write MANIFEST.md");
            println!("manifest-gen: wrote {}", out_path.display());
        }
        "manifest-check" => {
            let expected = render_manifest(&root);
            let manifest_path = root.join("MANIFEST.md");
            let actual = fs::read_to_string(&manifest_path).unwrap_or_default();
            if expected == actual {
                println!("manifest-check: OK -- MANIFEST.md matches the generated module graph");
            } else {
                eprintln!(
                    "ERROR: MANIFEST.md is stale (does not match what manifest-gen would \
                     produce right now)."
                );
                eprintln!(
                    "        Run `cargo run -p xtask --offline -- manifest-gen` and commit \
                     the result."
                );
                exit(1);
            }
        }
        other => {
            eprintln!("usage: cargo run -p xtask -- <boundary-lint|manifest-gen|manifest-check>");
            if !other.is_empty() {
                eprintln!("unknown command: {other}");
            }
            exit(2);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn boundary_lint_passes_on_this_workspace() {
        let root = workspace_root();
        assert_eq!(boundary_lint(&root), Ok(()));
    }

    #[test]
    fn manifest_is_not_stale() {
        let root = workspace_root();
        let expected = render_manifest(&root);
        let actual = fs::read_to_string(root.join("MANIFEST.md")).unwrap_or_default();
        assert_eq!(
            expected, actual,
            "MANIFEST.md is stale -- run `cargo run -p xtask -- manifest-gen`"
        );
    }
}
