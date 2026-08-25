#!/usr/bin/env python3
"""Objective scorer for one experiment run.

Everything here is computed by a program. No LLM judge, no human judgement.

  builds              cargo build succeeds
  base_tests_pass     the pre-existing test suite still passes (no regression)
  hidden_pass/total   the hidden acceptance tests (agent never saw them)
  duplication         re-implemented core primitives found outside core
  illegal_edges       domain -> domain dependencies in Cargo.toml
  loc_added           lines added versus the pristine base

Usage:  score.py <run_dir> [--base <pristine_base>] [--hidden <hidden_dir>] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAINS = {"users", "tasks", "notifier", "search", "projects", "tags",
           "comments", "labels", "attachments", "audit", "teams", "webhooks"}

# A re-implemented primitive is detected by its behavioural fingerprint, not by
# its name — a renamed copy is the failure mode a name-only rule misses.
# Strong signatures are unambiguous re-implementations and count toward the
# primary metric. Weak ones are reported but not counted: a bare 86400 can be
# legitimate arithmetic rather than a copied primitive, and counting it would
# inflate the score with false positives.
DUPLICATION_SIGNATURES = [
    (
        "base62 alphabet literal",
        re.compile(r"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ),
    ("base62 radix arithmetic", re.compile(r"[%/]\s*62\b")),
    ("timestamp display format", re.compile(r"d\{\}t\{\}")),
]

WEAK_SIGNATURES = [
    ("seconds-per-day literal", re.compile(r"\b86_?400\b")),
]


def run(cmd: list[str], cwd: Path, timeout: int = 300):
    try:
        return subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "timeout")


def count_tests(output: str) -> tuple[int, int]:
    passed = failed = 0
    for m in re.finditer(r"(\d+) passed; (\d+) failed", output):
        passed += int(m.group(1))
        failed += int(m.group(2))
    return passed, failed


def rust_sources(root: Path):
    return [
        p
        for p in root.rglob("*.rs")
        if "target" not in p.parts and "tests" not in p.parts and p.is_file()
    ]


def crate_of(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if len(parts) >= 2 and parts[0] == "crates":
        return parts[1]
    return None


def check_duplication(root: Path, signatures=None) -> list[str]:
    """Core primitives re-implemented outside the core crate."""
    findings = []
    for path in rust_sources(root):
        crate = crate_of(path, root)
        if crate in (None, "core", "corelib"):
            continue
        text = strip_test_modules(path.read_text(encoding="utf-8", errors="replace"))
        for label, pattern in signatures or DUPLICATION_SIGNATURES:
            if pattern.search(text):
                findings.append(f"{path.relative_to(root)}: {label}")
    return findings


# A capability that cannot be implemented without a core primitive implies an
# edge to that primitive. If the capability is present and the edge is absent,
# the primitive was re-implemented. This catches a re-implementation that looks
# nothing like the original — the case a fingerprint match misses entirely.
REQUIRED_EDGES = [
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"timefmt|format_ts"),
        "primitive": "corelib::timefmt::format_ts",
    },
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"\btruncate\b"),
        "primitive": "corelib::text::truncate",
    },
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"page_slice|paging"),
        "primitive": "corelib::paging::page_slice",
    },
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"validate_range"),
        "primitive": "corelib::validate::validate_range",
    },
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"escape_body"),
        "primitive": "corelib::escape::escape_body",
    },
    {
        "capability": re.compile(r"\bfn\s+build_digest\b"),
        "requires": re.compile(r"priority_label"),
        "primitive": "corelib::priority::priority_label",
    },
]

# Reaching into the legacy crate is a distinct failure from re-implementing:
# the agent found *a* helper, just the wrong one.
DECOY_USE = re.compile(r"\blegacy::\w+")


def check_missing_edges(root: Path) -> list[str]:
    """Capabilities implemented without the core primitive they require."""
    findings = []
    for path in rust_sources(root):
        crate = crate_of(path, root)
        if crate in (None, "core", "corelib"):
            continue
        text = strip_test_modules(path.read_text(encoding="utf-8", errors="replace"))
        for rule in REQUIRED_EDGES:
            if rule["capability"].search(text) and not rule["requires"].search(text):
                findings.append(
                    f"{path.relative_to(root)}: implements a capability that "
                    f"requires {rule['primitive']} without using it "
                    f"(re-implemented)"
                )
    return findings


def strip_test_modules(text: str) -> str:
    """Remove each `#[cfg(test)] mod tests { ... }` block, by brace matching.

    Test code legitimately contains literals like 86_400, so scanning it would
    produce false positives. But truncating at the first `#[cfg(test)]` would
    also discard any real code that appears AFTER the test module — and
    appending a new feature below the existing tests is a perfectly normal
    thing to do, which would make that code invisible to every structural
    check here. So each block is excised individually and the rest is kept.
    """
    out = []
    i = 0
    while True:
        start = text.find("#[cfg(test)]", i)
        if start == -1:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:start])
        brace = text.find("{", start)
        if brace == -1:
            return "".join(out)
        depth, j = 0, brace
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        i = j + 1


def check_illegal_edges(root: Path) -> list[str]:
    """Domain crates must depend on core only, never on each other."""
    findings = []
    for manifest in root.glob("crates/*/Cargo.toml"):
        crate = manifest.parent.name
        if crate not in DOMAINS:
            continue
        text = manifest.read_text(encoding="utf-8")
        for dep in re.findall(r"^(\w+)\s*=\s*\{\s*path", text, re.M):
            if dep in DOMAINS and dep != crate:
                findings.append(f"{crate} -> {dep}")
    return findings


def loc_added(run_dir: Path, base: Path) -> int:
    """Net lines of Rust added relative to the pristine base."""
    def total(root: Path) -> int:
        return sum(
            len(p.read_text(encoding="utf-8", errors="replace").splitlines())
            for p in rust_sources(root)
        )
    return total(run_dir) - total(base)


def score(run_dir: Path, base: Path, hidden: Path) -> dict:
    result: dict = {"run": run_dir.name}

    build = run(["cargo", "build", "-q"], run_dir)
    result["builds"] = build.returncode == 0
    if not result["builds"]:
        result["build_error"] = (build.stderr or "")[-400:]

    # Pre-existing suite must still pass: catches a "fix" that breaks the repo.
    if result["builds"]:
        base_tests = run(["cargo", "test", "-q"], run_dir)
        passed, failed = count_tests(base_tests.stdout + base_tests.stderr)
        result["base_tests_passed"] = passed
        result["base_tests_failed"] = failed
        result["base_tests_pass"] = failed == 0 and base_tests.returncode == 0
    else:
        result["base_tests_pass"] = False

    # Hidden acceptance tests, installed only now.
    total_hidden = len(re.findall(r"#\[test\]", hidden.read_text(encoding="utf-8")))
    result["hidden_total"] = total_hidden
    dest = run_dir / "crates" / "tasks" / "tests"
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(hidden, dest / hidden.name)
    ht = run(["cargo", "test", "-q", "-p", "tasks", "--test", hidden.stem], run_dir)
    hp, hf = count_tests(ht.stdout + ht.stderr)
    result["hidden_compiles"] = "error" not in (ht.stderr or "").lower() or hp + hf > 0
    result["hidden_passed"] = hp
    result["hidden_failed"] = hf
    if not result["hidden_compiles"]:
        result["hidden_error"] = (ht.stderr or "")[-400:]
    (dest / hidden.name).unlink(missing_ok=True)

    dup = check_duplication(run_dir) + check_missing_edges(run_dir)
    decoys = []
    for path in rust_sources(run_dir):
        if crate_of(path, run_dir) in (None, "core", "corelib", "legacy"):
            continue
        text = strip_test_modules(path.read_text(encoding="utf-8", errors="replace"))
        for m in set(DECOY_USE.findall(text)):
            decoys.append(f"{path.relative_to(run_dir)}: uses {m}")
    edges = check_illegal_edges(run_dir)
    result["duplication"] = dup
    result["duplication_count"] = len(dup)
    result["weak_signals"] = check_duplication(run_dir, WEAK_SIGNATURES)
    result["decoy_uses"] = decoys
    result["decoy_count"] = len(decoys)
    result["illegal_edges"] = edges
    result["illegal_edge_count"] = len(edges)
    result["loc_added"] = loc_added(run_dir, base)

    # Pre-registered ranking rule: correctness first, then duplication, then cost.
    result["correct"] = (
        result["builds"]
        and result.get("base_tests_pass", False)
        and result["hidden_passed"] == total_hidden
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--base", default=str(HERE / "base_v2"))
    ap.add_argument("--hidden", default=str(HERE / "hidden" / "hidden_digest.rs"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    r = score(Path(args.run_dir).resolve(), Path(args.base).resolve(), Path(args.hidden).resolve())

    if args.json:
        print(json.dumps(r, indent=2))
        return 0

    print(f"run: {r['run']}")
    print(f"  builds            {r['builds']}")
    print(f"  base tests pass   {r.get('base_tests_pass')}")
    print(f"  hidden            {r['hidden_passed']}/{r['hidden_total']}")
    print(f"  duplication       {r['duplication_count']}")
    for d in r["duplication"]:
        print(f"                      - {d}")
    print(f"  decoy uses        {r['decoy_count']}")
    for d in r["decoy_uses"]:
        print(f"                      - {d}")
    print(f"  illegal edges     {r['illegal_edge_count']}")
    for e in r["illegal_edges"]:
        print(f"                      - {e}")
    print(f"  loc added         {r['loc_added']}")
    print(f"  CORRECT           {r['correct']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
