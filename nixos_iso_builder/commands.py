"""Command implementations for NixOS ISO Builder"""

import shutil
import subprocess
from argparse import Namespace
from pathlib import Path

from .help_loader import get_burn_help, get_main_help
from .iso_utils import find_iso, validate_iso_is_file
from .logging_utils import log_error, log_info, log_success, log_warn
from .nix_utils import build_iso, cleanup_result_symlinks, command_exists, validate_log_level


def cmd_build(args: Namespace, script_dir: Path) -> int:
    """Build the NixOS ISO with specified logging profile"""
    # Get the log level from command-line argument (default: debug)
    log_level: str = getattr(args, "log_level", "debug")

    log_info(f"Building NixOS ISO with '{log_level}' logging profile...")
    log_info("First build: 15-30 minutes | Subsequent builds: 5-10 minutes")
    log_info(f"Build log: {script_dir / 'build.log'}")
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
    cleanup_result_symlinks(script_dir)

    # Build the ISO with tee behavior (output to both console and file)
    return_code = build_iso(script_dir, log_level, script_dir / "build.log")

    if return_code != 0:
        log_error("Build failed")
        return 1

    print()
    iso = find_iso(script_dir)
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


def cmd_clean(args: Namespace, script_dir: Path) -> int:
    """Clean build artifacts"""
    log_info("Cleaning build artifacts...")

    # Remove result directories
    patterns = ["result", "result-*", "mnt"]
    for pattern in patterns:
        for path in script_dir.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as e:
                pass  # Silently ignore errors like bash does

    log_success("Cleanup complete")
    return 0


def cmd_run(args: Namespace, script_dir: Path) -> int:
    """Boot ISO in QEMU"""
    log_info("Booting ISO in QEMU...")

    if not command_exists("qemu-system-x86_64"):
        log_error("QEMU not found")
        log_info("Install QEMU: sudo apt install qemu-system-x86")
        return 1

    iso = find_iso(script_dir)
    if not iso:
        log_error("ISO image not found — build one first with: python3 build.py build")
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
            ["qemu-system-x86_64", "-m", "512", "-display", "cocoa,full-screen=on", "-cdrom", iso],
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


def cmd_inspect(args: Namespace, script_dir: Path) -> int:
    """Inspect ISO contents"""
    log_info("Inspecting ISO contents...")

    iso = find_iso(script_dir)
    if not iso:
        log_error("ISO file not found")
        return 1

    log_info("Mounting ISO...")
    mnt_dir = script_dir / "mnt"

    try:
        mnt_dir.mkdir(exist_ok=True)
        subprocess.run(
            ["sudo", "mount", "-o", "loop", iso, str(mnt_dir)],
            check=True,
            capture_output=True,
        )
        log_success(f"ISO mounted at {mnt_dir}")
        log_info(f"Contents of {mnt_dir}:")
        subprocess.run(["ls", "-lhR", str(mnt_dir)], check=True)

        log_info("Unmounting ISO...")
        subprocess.run(["sudo", "umount", str(mnt_dir)], check=True, capture_output=True)
        log_success("ISO unmounted")
        return 0
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to mount ISO: {e}")
        return 1
    except Exception as e:
        log_error(f"Inspect error: {e}")
        return 1
    finally:
        # Clean up mount directory
        try:
            mnt_dir.rmdir()
        except Exception:
            pass


def cmd_burn_help(args: Namespace, script_dir: Path) -> int:
    """Show USB burning instructions"""
    print()
    print(get_burn_help())
    print()
    return 0


def cmd_help(args: Namespace, script_dir: Path) -> int:
    """Show help message"""
    print()
    print(get_main_help())
    print()
    return 0
