.PHONY: build test boundary-lint manifest-check manifest-gen run ci clean

build:
	./build.sh

test:
	./test.sh

boundary-lint:
	./tools/boundary-check.sh

manifest-check:
	./tools/generate-manifest.sh --check

manifest-gen:
	./tools/generate-manifest.sh

run: build
	./run.sh

ci:
	./ci.sh

clean:
	rm -rf out out-test tools/out
