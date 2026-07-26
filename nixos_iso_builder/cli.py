"""Command-line interface for NixOS ISO Builder"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .commands import (
    cmd_build,
    cmd_burn_help,
    cmd_clean,
    cmd_help,
    cmd_inspect,
    cmd_test,
)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="nixos-iso-builder",
        description="Build custom NixOS debug ISO images",
        add_help=False,  # We'll handle help manually
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Build NixOS ISO")
    build_parser.add_argument(
        "--log-level",
        default="debug",
        help="Logging profile: debug, info, production, minimal (default: debug)",
    )

    # Clean command
    subparsers.add_parser("clean", help="Remove build artifacts")

    # Test command
    subparsers.add_parser("test", help="Test ISO in QEMU")

    # Inspect command
    subparsers.add_parser("inspect", help="Mount and inspect ISO contents")

    # Burn help command
    subparsers.add_parser("burn-help", help="Show USB burning instructions")

    # Help command
    subparsers.add_parser("help", help="Show help message")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for CLI

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for error)
    """
    script_dir = Path(__file__).parent.parent.absolute()

    parser = create_parser()
    args = parser.parse_args(argv)

    # Command mapping
    commands = {
        "build": cmd_build,
        "clean": cmd_clean,
        "test": cmd_test,
        "inspect": cmd_inspect,
        "burn-help": cmd_burn_help,
        "help": cmd_help,
        None: cmd_help,  # Default to help
    }

    # Get the command function
    cmd_func = commands.get(args.command, cmd_help)

    # Execute command
    try:
        return cmd_func(args, script_dir)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
