#!/usr/bin/env python3
"""Objective scorer for the transitive-impact test.

The change itself is trivial. What is measured is whether the two INDIRECT
dependents were found — neither is reachable by grepping for the changed
function, and the compiler is silent about both.

  hidden      acceptance tests, installed only at scoring time
  sites       which of the three sites were actually updated
  false_green whether the repo's own pre-existing suite still passes while the
              hidden tests fail — i.e. the change looks done and is not
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

ACC_CARGO = """[package]
name = "_acceptance"
version = "0.1.0"
edition = "2021"

[dependencies]

[dev-dependencies]
corelib = { path = "../corelib" }
search = { path = "../search" }
webhooks = { path = "../webhooks" }
"""


def run(cmd, cwd, timeout=300):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", "timeout")


def count_tests(out: str):
    p = f = 0
    for m in re.finditer(r"(\d+) passed; (\d+) failed", out):
        p += int(m.group(1))
        f += int(m.group(2))
    return p, f


def install_acceptance(root: Path, hidden: Path) -> None:
    acc = root / "crates/_acceptance"
    (acc / "tests").mkdir(parents=True, exist_ok=True)
    (acc / "src").mkdir(parents=True, exist_ok=True)
    (acc / "src/lib.rs").write_text("\n")
    (acc / "Cargo.toml").write_text(ACC_CARGO)
    shutil.copy(hidden, acc / "tests" / hidden.name)
    ws = root / "Cargo.toml"
    s = ws.read_text()
    if "_acceptance" not in s:
        ws.write_text(s.replace("members = [", 'members = ["crates/_acceptance", '))


def remove_acceptance(root: Path) -> None:
    shutil.rmtree(root / "crates/_acceptance", ignore_errors=True)
    ws = root / "Cargo.toml"
    ws.write_text(ws.read_text().replace('"crates/_acceptance", ', ""))


def _unused_sites(root: Path) -> dict:
    """Which of the three sites the change actually reached."""
    esc = (root / "crates/corelib/src/escape.rs").read_text()
    srch = (root / "crates/search/src/lib.rs").read_text()
    wh = (root / "crates/webhooks/src/lib.rs").read_text()
    return {
        "escape_body": "':'" in esc or '":"' in esc,
        # the inverse must decode the new escape
        "unescape_body": bool(re.search(r"Some\('?:'?\)|'\\\\:'|\":\"", srch)),
        # the splitter must stop treating an escaped colon as a delimiter
        "split_headers": "split_once(':')" not in wh,
    }


def score(root: Path, hidden: Path) -> dict:
    r = {"run": root.name}
    remove_acceptance(root)

    build = run(["cargo", "build", "-q"], root)
    r["builds"] = build.returncode == 0
    if not r["builds"]:
        r["build_error"] = (build.stderr or "")[-300:]

    base = run(["cargo", "test", "-q", "--workspace"], root)
    bp, bf = count_tests(base.stdout + base.stderr)
    r["base_tests_passed"], r["base_tests_failed"] = bp, bf
    r["base_tests_pass"] = bf == 0 and base.returncode == 0

    total = len(re.findall(r"#\[test\]", hidden.read_text()))
    install_acceptance(root, hidden)
    ht = run(["cargo", "test", "-q", "-p", "_acceptance", "--test", hidden.stem], root)
    hp, hf = count_tests(ht.stdout + ht.stderr)
    r["hidden_total"] = total
    r["hidden_passed"] = hp
    r["hidden_failed"] = hf
    if hp + hf == 0:
        r["hidden_error"] = (ht.stderr or "")[-300:]
    remove_acceptance(root)

    r["sites"] = {}
    r["sites_updated"] = 0
    r["correct"] = r["builds"] and r["base_tests_pass"] and hp == total
    # the failure mode this experiment exists to detect
    r["false_green"] = r["base_tests_pass"] and hp < total
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--hidden", default=str(HERE / "hidden" / "hidden_length.rs"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = score(Path(a.run_dir).resolve(), Path(a.hidden).resolve())
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        s = {}
        print(f"{res['run']:11} hidden={res['hidden_passed']}/{res['hidden_total']} "
              f"correct={res['correct']} false_green={res['false_green']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
