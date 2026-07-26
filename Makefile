.PHONY: help build build-debug build-info build-prod build-minimal clean test inspect burn-help check lint install-dev

help:
	@echo "NixOS Debug ISO Build System - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make help           - Show this help message"
	@echo "  make build          - Build ISO with debug logging (default)"
	@echo "  make build-debug    - Build with debug profile (max verbosity)"
	@echo "  make build-info     - Build with info profile (balanced logging)"
	@echo "  make build-prod     - Build with production profile (minimal logs)"
	@echo "  make build-minimal  - Build with minimal profile (quiet mode)"
	@echo "  make clean          - Remove build artifacts (result/, mnt/)"
	@echo "  make test           - Boot ISO in QEMU for testing"
	@echo "  make inspect        - Mount and inspect ISO contents"
	@echo "  make burn-help      - Show USB burning instructions"
	@echo "  make check          - Run mypy with strict type checking"
	@echo "  make lint           - Run all linting/checking (mypy)"
	@echo "  make install-dev    - Install development dependencies (mypy)"
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
	@echo "  make test           # Test in QEMU"

build:
	@python3 build.py build

build-debug:
	@python3 build.py build --log-level debug

build-info:
	@python3 build.py build --log-level info

build-prod:
	@python3 build.py build --log-level production

build-minimal:
	@python3 build.py build --log-level minimal

clean:
	@python3 build.py clean

test:
	@python3 build.py test

inspect:
	@python3 build.py inspect

burn-help:
	@python3 build.py burn-help

check:
	@echo "🔍 Running mypy strict type checking..."
	@mypy build.py nixos_iso_builder/ --strict --show-error-codes --pretty --warn-unused-ignores
	@echo "✅ Type check passed!"

lint: check
	@echo "✅ All checks passed!"

install-dev:
	@echo "📦 Installing development dependencies..."
	@pip install --upgrade mypy
	@echo "✅ Development dependencies installed!"

.DEFAULT_GOAL := help
