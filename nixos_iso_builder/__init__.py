"""NixOS ISO Builder - Build custom NixOS debug ISOs

Modules:
- logging_utils: Colored logging utilities
- iso_utils: ISO file discovery and validation
- nix_utils: Nix-related utilities
- commands: Command implementations
- cli: Command-line interface
"""

__version__ = "1.0.0"
__author__ = "NixOS ISO Builder Contributors"

from .cli import create_parser, main
from .commands import cmd_build, cmd_clean, cmd_help, cmd_inspect, cmd_test
from .iso_utils import find_iso, validate_iso_is_file
from .logging_utils import log_error, log_info, log_success, log_warn

__all__ = [
    "main",
    "create_parser",
    "cmd_build",
    "cmd_clean",
    "cmd_test",
    "cmd_inspect",
    "cmd_help",
    "find_iso",
    "validate_iso_is_file",
    "log_info",
    "log_success",
    "log_warn",
    "log_error",
]
