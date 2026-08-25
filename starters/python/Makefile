PY := python3

.PHONY: build test boundary-lint manifest manifest-check ci run

# "build" for a pure-stdlib Python project = "does everything parse/compile cleanly".
build:
	$(PY) -m compileall -q core domains app tools

test:
	$(PY) -m unittest discover -s . -p 'test_*.py' -v

# Runs the always-available stdlib enforcer, and additionally runs
# import-linter's declarative contracts (.importlinter) when installed.
boundary-lint:
	$(PY) -m tools.boundary_check
	@if command -v lint-imports >/dev/null 2>&1; then \
		echo "--- import-linter (.importlinter) ---"; \
		lint-imports --config .importlinter; \
	else \
		echo "--- import-linter not installed offline; skipping (optional) ---"; \
		echo "    .importlinter still documents the same contracts declaratively;"; \
		echo "    tools/boundary_check.py above is the enforced, dependency-free gate."; \
	fi

# Regenerate manifest.json from the real module graph.
manifest:
	$(PY) -m tools.gen_manifest

# Fail if manifest.json is stale relative to the current source tree
# (i.e. code changed but nobody ran `make manifest`).
manifest-check:
	$(PY) -m tools.gen_manifest --check

run:
	$(PY) -m app.main

ci: build test boundary-lint manifest-check
	@echo "ci: build + test + boundary-lint + manifest-drift-check all passed"
