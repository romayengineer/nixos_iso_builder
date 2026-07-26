.PHONY: help build clean test inspect burn-help check lint format install-dev

help:
	@echo "NixOS Debug ISO Build System - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make help           - Show this help message"
	@echo "  make build          - Build the custom NixOS ISO with debug logging"
	@echo "  make clean          - Remove build artifacts (result/, mnt/)"
	@echo "  make test           - Boot ISO in QEMU for testing"
	@echo "  make inspect        - Mount and inspect ISO contents"
	@echo "  make burn-help      - Show USB burning instructions"
	@echo "  make check          - Run mypy with strict type checking"
	@echo "  make lint           - Run all linting/checking (mypy)"
	@echo "  make install-dev    - Install development dependencies (mypy)"
	@echo ""
	@echo "Example workflow:"
	@echo "  make install-dev    # First time only"
	@echo "  make check          # Check for type errors"
	@echo "  make build          # Build the ISO"
	@echo "  make test           # Test in QEMU"

build:
	@python3 build.py build

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
	@mypy build.py --strict --show-error-codes --pretty --warn-unused-ignores
	@echo "✅ Type check passed!"

lint: check
	@echo "✅ All checks passed!"

install-dev:
	@echo "📦 Installing development dependencies..."
	@pip install --upgrade mypy
	@echo "✅ Development dependencies installed!"

.DEFAULT_GOAL := help
