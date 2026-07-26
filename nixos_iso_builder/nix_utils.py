"""Nix-related utilities"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from .logging_utils import log_error, log_info, log_warn


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> int:
    """Run a command and return exit code

    Args:
        cmd: Command and arguments as list
        cwd: Working directory for command
        check: Whether to check return code

    Returns:
        Exit code from command
    """
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        log_error(f"Command not found: {cmd[0]}")
        return 1


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH

    Args:
        cmd: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    return shutil.which(cmd) is not None


def validate_log_level(log_level: str) -> bool:
    """Validate the log level argument

    Args:
        log_level: Log level string to validate

    Returns:
        True if valid, False otherwise
    """
    valid_levels = {"debug", "info", "production", "minimal"}
    if log_level not in valid_levels:
        log_error(f"Invalid log level: {log_level}")
        log_info(f"Valid levels: {', '.join(sorted(valid_levels))}")
        return False
    return True


def cleanup_result_symlinks(script_dir: Path) -> None:
    """Clean up old result symlinks before building

    Args:
        script_dir: Directory containing result* symlinks
    """
    for result_path in script_dir.glob("result*"):
        try:
            if result_path.is_symlink() or result_path.is_file():
                result_path.unlink()
                log_info(f"Removed old result: {result_path.name}")
        except Exception as e:
            log_warn(f"Failed to remove {result_path.name}: {e}")


def build_iso(
    script_dir: Path,
    log_level: str,
    logfile_path: Path,
) -> int:
    """Build the NixOS ISO using nix build

    Args:
        script_dir: Directory to build in
        log_level: Logging profile to use
        logfile_path: Path to write build log to

    Returns:
        Exit code from nix build command
    """
    flake_output = f".#bootDebugISO-{log_level}"

    try:
        with open(logfile_path, "w") as logfile:
            process = subprocess.Popen(
                [
                    "nix",
                    "build",
                    "--extra-experimental-features",
                    "nix-command flakes",
                    "--print-out-paths",
                    "--print-build-logs",
                    "--rebuild",
                    flake_output,
                ],
                cwd=script_dir,
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
            return process.returncode
    except FileNotFoundError:
        log_error("nix command not found")
        return 1
    except Exception as e:
        log_error(f"Build error: {e}")
        return 1
