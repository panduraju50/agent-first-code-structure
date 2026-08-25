.PHONY: build test lint-boundaries manifest-generate manifest-check ci

# Offline: tsc + node stdlib only, no npm install required.
build:
	tsc -p tsconfig.build.json

test: build
	node --test 'dist/**/*.test.js' 'scripts/**/*.test.mjs'

lint-boundaries:
	node scripts/check-boundaries.mjs

manifest-generate:
	node scripts/generate-manifest.mjs

manifest-check:
	node scripts/generate-manifest.mjs --check

# build + test + boundary-lint + manifest-drift-check
ci: build test lint-boundaries manifest-check
	@echo "CI OK: build + test + boundary-lint + manifest-drift-check all passed"
