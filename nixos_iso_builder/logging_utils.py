"""Logging utilities for NixOS ISO Builder"""

# Colors for output
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color


def log_info(message: str) -> None:
    """Log info message with blue ℹ"""
    print(f"{BLUE}ℹ{NC} {message}")


def log_success(message: str) -> None:
    """Log success message with green ✅"""
    print(f"{GREEN}✅{NC} {message}")


def log_warn(message: str) -> None:
    """Log warning message with yellow ⚠"""
    print(f"{YELLOW}⚠{NC}  {message}")


def log_error(message: str) -> None:
    """Log error message with red ✗"""
    print(f"{RED}✗{NC}  {message}")
