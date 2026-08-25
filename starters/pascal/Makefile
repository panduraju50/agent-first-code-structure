SRC_DIR  := src
BIN_DIR  := bin
FPC      ?= fpc
FPCFLAGS := -Fu$(SRC_DIR) -FE$(BIN_DIR) -Fu$(BIN_DIR)

.PHONY: build test boundary-lint manifest manifest-check ci clean

build: $(BIN_DIR)
	$(FPC) $(FPCFLAGS) $(SRC_DIR)/app.pas

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Compiles each test program (fpc auto-resolves unit deps via -Fu$(SRC_DIR))
# and runs it. A test binary exits non-zero on any failed Check(), which
# fails `make test`.
test: $(BIN_DIR)
	$(FPC) $(FPCFLAGS) tests/test_core.pas
	$(FPC) $(FPCFLAGS) tests/test_users.pas
	$(FPC) $(FPCFLAGS) tests/test_tasks.pas
	$(BIN_DIR)/test_core
	$(BIN_DIR)/test_users
	$(BIN_DIR)/test_tasks

# The Design D boundary enforcer: no domain-to-domain uses, no duplicate
# core primitives. See tools/boundary_lint.sh.
boundary-lint:
	./tools/boundary_lint.sh

# Regenerates manifest.json from the real src/*.pas module graph.
manifest:
	./tools/gen_manifest.sh > manifest.json

# CI-facing check: fails if manifest.json doesn't match what gen_manifest.sh
# would produce right now, i.e. someone changed src/*.pas without running
# `make manifest` and committing the result.
manifest-check:
	./tools/check_manifest_drift.sh

# The full gate: build + test + boundary-lint + manifest-drift-check.
ci: boundary-lint manifest-check build test

clean:
	rm -rf $(BIN_DIR) *.o *.ppu src/*.o src/*.ppu tests/*.o tests/*.ppu
