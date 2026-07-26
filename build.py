#!/usr/bin/env python3
"""
NixOS Debug ISO Build Script (Python version)
Usage: ./build.py <command> [args]
Commands: build, clean, test, inspect, burn-help, help
"""

import argparse
import shutil
import subprocess
import sys
from glob import glob
from pathlib import Path
from typing import List, Optional

# ============================================================================
# CONSTANTS
# ============================================================================

# Colors for output
BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color

# Script directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


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


def find_iso() -> Optional[str]:
    """Find the built ISO file, return path or None
    
    Searches for ISO files in this order:
    1. result/iso/ (standard output location)
    2. result symlink directly (if it's a file)
    3. ANY ISO in /nix/store under result links or recent paths
    4. Latest ISO anywhere in /nix/store (fallback)
    """
    # Try result/iso/ first
    result_link = SCRIPT_DIR / "result"
    iso_dir = result_link / "iso"
    if iso_dir.exists() and iso_dir.is_dir():
        isos = sorted(iso_dir.glob("nixos-*.iso"))
        if isos:
            return str(isos[0])
    
    # Check if result itself is a direct ISO file
    if result_link.exists() and result_link.is_file() and result_link.suffix == ".iso":
        return str(result_link)
    
    # Fallback: Check all result-* symlinks
    nix_store = Path("/nix/store")
    for result_variant in SCRIPT_DIR.glob("result*"):
        if result_variant.is_symlink():
            target_iso_dir = result_variant / "iso"
            if target_iso_dir.exists() and target_iso_dir.is_dir():
                isos = sorted(target_iso_dir.glob("nixos-*.iso"))
                if isos:
                    return str(isos[0])
    
    # Ultimate fallback: Find any ISO anywhere in /nix/store (newest first)
    if nix_store.exists():
        iso_files: List[Path] = []
        # Search for any nixos ISO file
        for iso_path in nix_store.glob("**/*.iso"):
            if iso_path.is_file() and "nixos" in str(iso_path):
                iso_files.append(iso_path)
        
        if iso_files:
            # Sort by modification time, newest first
            iso_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            log_warn(f"Using fallback ISO from nix store: {iso_files[0]}")
            return str(iso_files[0])

    return None


def validate_iso_is_file(iso_path: str) -> bool:
    """Validate that the ISO path is an actual file (not a directory)
    
    Args:
        iso_path: Path to the ISO file
        
    Returns:
        True if ISO is a regular file and exists, False otherwise
    """
    path = Path(iso_path)
    
    if not path.exists():
        log_error(f"ISO file does not exist: {iso_path}")
        return False
    
    if not path.is_file():
        log_error(f"ISO path is not a file (is it a directory?): {iso_path}")
        log_info(f"Expected: regular file")
        log_info(f"Actual: {path.stat().st_mode:o} ({path}")
        return False
    
    return True


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> int:
    """Run a command and return exit code"""
    try:
        result = subprocess.run(cmd, cwd=cwd or SCRIPT_DIR, check=False)
        return result.returncode
    except FileNotFoundError:
        log_error(f"Command not found: {cmd[0]}")
        return 1


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH"""
    result = subprocess.run(["which", cmd], capture_output=True)
    return result.returncode == 0


def validate_log_level(log_level: str) -> bool:
    """Validate that the log level is supported

    Args:
        log_level: One of "debug", "production", "info", "minimal"

    Returns:
        True if valid, False otherwise
    """
    valid_levels = {"debug", "production", "info", "minimal"}
    if log_level not in valid_levels:
        log_error(
            f"Invalid log level: {log_level}. Must be one of: {', '.join(valid_levels)}"
        )
        return False
    return True


# ============================================================================
# BUILD FUNCTIONS
# ============================================================================


def cmd_build(args: argparse.Namespace) -> int:
    """Build the NixOS ISO with specified logging profile"""
    # Get the log level from command-line argument (default: debug)
    log_level: str = getattr(args, "log_level", "debug")

    log_info(f"Building NixOS ISO with '{log_level}' logging profile...")
    log_info("First build: 15-30 minutes | Subsequent builds: 5-10 minutes")
    log_info(f"Build log: {SCRIPT_DIR / 'build.log'}")
    print()

    # Check if nix is installed
    if not command_exists("nix"):
        log_error("Nix not found in PATH")
        log_info("Install Nix: https://nixos.org/download/")
        return 1

    # Validate the log level
    if not validate_log_level(log_level):
        return 1

    # Clean up old result symlinks before building
    # This ensures we get a fresh build and correct symlink
    for result_path in SCRIPT_DIR.glob("result*"):
        try:
            if result_path.is_symlink() or result_path.is_file():
                result_path.unlink()
                log_info(f"Removed old result: {result_path.name}")
        except Exception as e:
            log_warn(f"Failed to remove {result_path.name}: {e}")

    # Map log level to flake output name
    flake_output = f".#bootDebugISO-{log_level}"

    # Build the ISO with tee behavior (output to both console and file)
    # Using --print-out-paths to get the actual store path
    # Using --print-build-logs to capture all build output
    try:
        with open(SCRIPT_DIR / "build.log", "w") as logfile:
            process = subprocess.Popen(
                [
                    "nix",
                    "build",
                    "--extra-experimental-features",
                    "nix-command flakes",
                    "--print-out-paths",
                    "-L",  # Alias for --print-build-logs
                    flake_output,
                ],
                cwd=SCRIPT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output to both console and file
            assert process.stdout is not None, "process.stdout should not be None"
            for line in process.stdout:
                print(line, end="")
                logfile.write(line)
                logfile.flush()

            process.wait()

            if process.returncode != 0:
                log_error("Build failed")
                return 1
    except FileNotFoundError:
        log_error("nix command not found")
        return 1
    except Exception as e:
        log_error(f"Build error: {e}")
        return 1

    print()
    iso = find_iso()
    if iso:
        log_info(f"ISO location: {iso}")
        
        # Validate that the ISO is actually a file
        if not validate_iso_is_file(iso):
            log_error("Build completed but ISO validation failed")
            return 1
        
        log_success("Build complete!")
        # Show file details
        iso_path = Path(iso)
        size_mb = iso_path.stat().st_size / (1024 * 1024)
        owner = iso_path.owner()  # type: ignore
        group = iso_path.group()  # type: ignore
        print(
            f"{iso_path.stat().st_mode:o} {owner:>8} {group:>8} {size_mb:>6.1f}M {iso_path.name}"
        )
        return 0
    else:
        log_error("ISO file not found after build")
        return 1


def cmd_clean(args: argparse.Namespace) -> int:
    """Clean build artifacts"""
    log_info("Cleaning build artifacts...")

    # Remove result directories
    patterns = ["result", "result-*", "mnt"]
    for pattern in patterns:
        for path in SCRIPT_DIR.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as e:
                pass  # Silently ignore errors like bash does

    log_success("Cleanup complete")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    """Test ISO in QEMU"""
    log_info("Testing ISO in QEMU...")

    if not command_exists("qemu-system-x86_64"):
        log_error("QEMU not found")
        log_info("Install QEMU: sudo apt install qemu-system-x86")
        return 1

    iso = find_iso()
    if not iso:
        log_info("ISO not found, building first...")
        if cmd_build(args) != 0:
            return 1
        iso = find_iso()
        if not iso:
            log_error("ISO still not found after build")
            return 1

    log_info(f"Using ISO: {iso}")

    # Verify the ISO file actually exists and is a regular file
    if not validate_iso_is_file(iso):
        log_info(
            "File verification failed - ISO may have been garbage collected by Nix"
        )
        return 1

    iso_path = Path(iso)
    log_info(f"ISO file verified ({iso_path.stat().st_size / (1024**3):.2f} GB)")
    log_info("Starting QEMU (Ctrl+C to exit)...")
    log_info(
        "Note: Running without -enable-kvm (KVM not available in WSL, will use TCG - slower)"
    )
    print()

    # Try to run QEMU without KVM
    try:
        subprocess.run(
            ["qemu-system-x86_64", "-m", "512", "-cdrom", iso],
            check=False,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        log_error("QEMU not found")
        return 1
    except Exception as e:
        log_warn(f"QEMU error: {e}")
        return 1

    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect ISO contents by mounting"""
    log_info("Inspecting ISO contents...")

    iso = find_iso()
    if not iso:
        log_info("ISO not found, building first...")
        if cmd_build(args) != 0:
            return 1
        iso = find_iso()
        if not iso:
            log_error("ISO still not found after build")
            return 1

    mnt_dir = SCRIPT_DIR / "mnt"

    try:
        # Create mount directory
        mnt_dir.mkdir(exist_ok=True)

        # Mount ISO
        log_info("Mounting ISO...")
        result = subprocess.run(
            ["sudo", "mount", "-o", "loop", iso, str(mnt_dir)], check=False
        )
        if result.returncode != 0:
            log_error("Failed to mount ISO")
            return 1

        print()
        log_info("ISO contents:")
        # List directory contents
        subprocess.run(["ls", "-lah", str(mnt_dir)], check=False)

        print()
        log_info("Unmounting ISO...")
        result = subprocess.run(["sudo", "umount", str(mnt_dir)], check=False)
        if result.returncode != 0:
            log_error("Failed to unmount ISO")
            return 1

        # Remove mount directory
        mnt_dir.rmdir()

        log_success("Inspection complete")
        return 0
    except Exception as e:
        log_error(f"Inspection error: {e}")
        return 1


def cmd_burn_help(args: argparse.Namespace) -> int:
    """Show USB burning instructions"""
    iso = find_iso()
    iso_display = iso or "<build the ISO first with: ./build.py build>"

    help_text = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                      USB BURNING INSTRUCTIONS                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

1. IDENTIFY YOUR USB DEVICE
   ━━━━━━━━━━━━━━━━━━━━━━━━━
   List all devices:
     lsblk
   
   Or use:
     sudo fdisk -l
   
   ⚠  Look for your USB device (usually /dev/sdX where X is a letter)
   ⚠  DO NOT confuse with your main hard drive!

2. UNMOUNT USB (if already mounted)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   sudo umount /dev/sdX*

3. BURN ISO TO USB
   ━━━━━━━━━━━━━━━━━
   
   METHOD A: Command Line (dd)
   ───────────────────────────
   sudo dd if={iso_display} of=/dev/sdX bs=4M status=progress conv=fsync
   sudo sync
   
   METHOD B: GUI Tools
   ──────────────────
   Use one of these applications:
     - GNOME Disks (gnome-disk-utility)
     - Balena Etcher (balena-etcher)
     - Popsicle
     - UNetbootin
   
   Steps:
     1. Open the application
     2. Select your ISO file from result/iso/
     3. Select your USB device
     4. Click Write/Burn/Start

4. EJECT USB SAFELY
   ━━━━━━━━━━━━━━━━
   sudo eject /dev/sdX

╔═══════════════════════════════════════════════════════════════════════════╗
║                              ⚠  WARNING  ⚠                                ║
║                                                                            ║
║  Replace /dev/sdX with YOUR ACTUAL USB DEVICE!                            ║
║  Using the wrong device will overwrite your data permanently!             ║
║                                                                            ║
║  Double-check lsblk output before running dd command.                     ║
╚═══════════════════════════════════════════════════════════════════════════╝

"""
    print(help_text)
    return 0


def cmd_help(args: argparse.Namespace) -> int:
    """Show help message"""
    help_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║           NixOS Debug ISO Build Script - Help                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE
━━━━━
  ./build.py <command> [args]

COMMANDS
━━━━━━━━
  build           Build the custom NixOS ISO with debug logging
  clean           Remove build artifacts (result/, mnt/)
  test            Boot ISO in QEMU for testing (requires QEMU)
  inspect         Mount and inspect ISO contents
  burn-help       Show detailed USB burning instructions
  help            Display this help message

EXAMPLES
━━━━━━━━
  # Build the ISO (first: 15-30 min, subsequent: 5-10 min)
  ./build.py build

  # Test the ISO in QEMU
  ./build.py test

  # Inspect what's inside the ISO
  ./build.py inspect

  # Get USB burning instructions
  ./build.py burn-help

  # Remove build artifacts to start fresh
  ./build.py clean

WORKFLOW
━━━━━━━
  1. Build:      ./build.py build
  2. Inspect:    ./build.py inspect
  3. Test:       ./build.py test
  4. Burn:       ./build.py burn-help    (then follow instructions)
  5. Boot & Debug: Boot from USB, run 'journalctl --boot --all'

NOTES
━━━━━
  • First build requires internet (downloads nixpkgs dependencies)
  • Subsequent builds are much faster (uses cache)
  • ISO size: ~900MB
  • Build space needed: ~15GB
  • Nix must be installed: https://nixos.org/download/

"""
    print(help_text)
    return 0


# ============================================================================
# MAIN DISPATCHER
# ============================================================================


def main() -> int:
    """Main entry point with argparse dispatch"""
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="NixOS Debug ISO Build Script",
        add_help=False,  # We handle help manually
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add subcommands
    build_parser = subparsers.add_parser(
        "build", help="Build the custom NixOS ISO with debug logging"
    )
    build_parser.add_argument(
        "--log-level",
        choices=["debug", "production", "info", "minimal"],
        default="debug",
        help="Logging profile to use (default: debug)",
    )

    subparsers.add_parser("clean", help="Remove build artifacts")
    subparsers.add_parser("test", help="Boot ISO in QEMU for testing")
    subparsers.add_parser("inspect", help="Mount and inspect ISO contents")
    subparsers.add_parser("burn-help", help="Show USB burning instructions")
    subparsers.add_parser("help", help="Show this help message")

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to appropriate command
    if not args.command or args.command == "help":
        return cmd_help(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "clean":
        return cmd_clean(args)
    elif args.command == "test":
        return cmd_test(args)
    elif args.command == "inspect":
        return cmd_inspect(args)
    elif args.command == "burn-help":
        return cmd_burn_help(args)
    else:
        log_error(f"Unknown command: {args.command}")
        print()
        return cmd_help(args)


if __name__ == "__main__":
    sys.exit(main())
