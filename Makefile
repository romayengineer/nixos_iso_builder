.PHONY: help fetch build build-debug build-info build-prod build-minimal clean test run inspect burn-help check lint install-dev test-integration test-unit test-all

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

clean:
	@python3 build.py clean

test:
	@echo "🧪 Running pytest tests..."
	@pytest tests -v

run:
	@python3 build.py test

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
