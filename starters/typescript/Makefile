.PHONY: build test lint-boundaries check-manifest generate-manifest ci start clean

build:
	npm run build

test:
	npm run test

lint-boundaries:
	npm run lint:boundaries

check-manifest:
	npm run check:manifest

generate-manifest:
	npm run generate:manifest

start:
	npm run start

clean:
	npm run clean

# Mirrors .github/workflows/ci.yml: build + test + boundary-lint + manifest-drift-check.
ci: build test lint-boundaries check-manifest
