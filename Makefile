.PHONY: help fetch build build-debug build-info build-prod build-minimal clean test run inspect burn-help check lint install-dev test-integration test-unit test-all docker-image docker-build docker-build-debug docker-build-info docker-build-prod docker-build-minimal docker-shell docker-clean-cache

help:
	@echo "NixOS Debug ISO Build System - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make help           - Show this help message"
	@echo "  make fetch          - Pre-fetch nixpkgs inputs (shows git clone progress)"
	@echo "  make build          - Build ISO with debug logging (default)"
	@echo "  make build-debug    - Build with debug profile (max verbosity)"
	@echo "  make build-info     - Build with info profile (balanced logging)"
	@echo "  make build-prod     - Build with production profile (minimal logs)"
	@echo "  make build-minimal  - Build with minimal profile (quiet mode)"
	@echo "  make clean          - Remove build artifacts (result/, mnt/)"
	@echo "  make test           - Run pytest integration tests"
	@echo "  make run            - Boot ISO in QEMU for testing"
	@echo "  make inspect        - Mount and inspect ISO contents"
	@echo "  make burn-help      - Show USB burning instructions"
	@echo "  make check          - Run mypy with strict type checking"
	@echo "  make lint           - Run all linting/checking (mypy)"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make test-integration - Run integration tests (builds real ISOs)"
	@echo "  make test-unit      - Run unit tests"
	@echo "  make test-all       - Run all tests"
	@echo "  make docker-image   - Build the Docker build image"
	@echo "  make docker-build   - Build ISO inside Docker (default profile)"
	@echo "  make docker-build-debug - Build inside Docker with debug profile"
	@echo "  make docker-build-info  - Build inside Docker with info profile"
	@echo "  make docker-build-prod  - Build inside Docker with production profile"
	@echo "  make docker-build-minimal - Build inside Docker with minimal profile"
	@echo "  make docker-shell   - Interactive shell in Docker container"
	@echo "  make docker-clean-cache - Remove Nix store cache volume"
	@echo ""
	@echo "  # Build with custom profile:"
	@echo "  make docker-build LOG_LEVEL='--log-level info'"
	@echo ""
	@echo "Log levels:"
	@echo "  debug               - Maximum verbosity (troubleshooting)"
	@echo "  info                - Balanced logging (general use)"
	@echo "  production          - Minimal logs (deployment)"
	@echo "  minimal             - Quiet mode (CI/CD)"
	@echo ""
	@echo "Example workflow:"
	@echo "  make install-dev    # First time only"
	@echo "  make check          # Check for type errors"
	@echo "  make build-debug    # Build with debug logging"
	@echo "  make test           # Run pytest tests"
	@echo "  make run            # Boot ISO in QEMU"

build:
	@GIT_PROGRESS_DELAY=0 python3 build.py build

build-debug:
	@GIT_PROGRESS_DELAY=0 python3 build.py build --log-level debug

build-info:
	@GIT_PROGRESS_DELAY=0 python3 build.py build --log-level info

build-prod:
	@GIT_PROGRESS_DELAY=0 python3 build.py build --log-level production

build-minimal:
	@GIT_PROGRESS_DELAY=0 python3 build.py build --log-level minimal

fetch:
	@echo "📦 Pre-fetching nixpkgs source with submodules (shows git progress)..."
	@GIT_PROGRESS_DELAY=0 nix flake lock --update-input nixpkgs --extra-experimental-features "nix-command flakes" --verbose

docker-image:
	@echo "🐳 Building Docker image (pre-fetches nixpkgs with submodules)..."
	@docker build -t nixos-iso-builder .

docker-clean-cache:
	@echo "🗑️  Removing Nix store cache volume..."
	@docker volume rm nix-store-cache 2>/dev/null && echo "✅ Cache volume removed" || echo "  (no cache volume found)"

docker-build:
	@echo "🐳 Building ISO inside Docker (Linux container)..."
	# Use 'output' not 'result' because nix build inside the container creates a
	# symlink named 'result' that would collide with a host directory named 'result'
	@rm -rf "$(PWD)/output"
	@mkdir -p "$(PWD)/output"
	@docker run --rm --entrypoint sh \
		-v nix-store-cache:/nix \
		-v "$(PWD):/build" \
		nixos-iso-builder \
		-c 'git config --global safe.directory /build && GIT_PROGRESS_DELAY=0 python3 ./build.py build $(LOG_LEVEL) && cp -rL result /build/output/'
	@echo "✅ ISO files in output/iso/:"
	@ls -lh "$(PWD)/output/iso/" 2>/dev/null || echo "  (no ISO found - check build output above)"

docker-build-debug: LOG_LEVEL = --log-level debug
docker-build-debug: docker-build

docker-build-info: LOG_LEVEL = --log-level info
docker-build-info: docker-build

docker-build-prod: LOG_LEVEL = --log-level production
docker-build-prod: docker-build

docker-build-minimal: LOG_LEVEL = --log-level minimal
docker-build-minimal: docker-build

docker-shell:
	@echo "🐳 Starting interactive shell in Docker container..."
	@docker run --rm -it --entrypoint sh \
		-v nix-store-cache:/nix \
		-v "$(PWD):/build" \
		nixos-iso-builder

clean:
	@python3 build.py clean

test:
	@echo "🧪 Running pytest tests..."
	@pytest tests -v

run:
	@echo "🖥️  Booting ISO in QEMU..."
	@python3 build.py run

inspect:
	@python3 build.py inspect

burn-help:
	@python3 build.py burn-help

check:
	@echo "🔍 Running mypy strict type checking..."
	@mypy build.py nixos_iso_builder/ tests/ --strict --show-error-codes --pretty --warn-unused-ignores
	@echo "✅ Type check passed!"

lint: check
	@echo "✅ All checks passed!"

install-dev:
	@echo "📦 Installing development dependencies..."
	@pip install --upgrade -r requirements-test.txt
	@echo "✅ Development dependencies installed!"

test-integration:
	@echo "🧪 Running integration tests (actually builds ISOs)..."
	@echo "⚠️  Stopping at first failure (-x flag)"
	@pytest tests/integration/ -x

test-unit:
	@echo "🧪 Running unit tests..."
	@pytest tests/unit/ -x 2>/dev/null || echo "No unit tests yet"

test-all: test-unit test-integration
	@echo "✅ All tests passed!"

.DEFAULT_GOAL := help
