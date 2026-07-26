"""ISO file finding and validation utilities"""

from pathlib import Path
from typing import List, Optional

from .logging_utils import log_error, log_warn


def find_iso(script_dir: Path) -> Optional[str]:
    """Find the built ISO file, return path or None

    Searches for ISO files in this order:
    1. result/iso/ (standard output location)
    2. result symlink directly (if it's a file)
    3. ANY ISO in /nix/store under result links or recent paths
    4. Latest ISO anywhere in /nix/store (fallback)

    Args:
        script_dir: Directory to search from (usually where build.py is located)

    Returns:
        Path to ISO file as string, or None if not found
    """
    # Try result/iso/ first
    result_link = script_dir / "result"
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
    for result_variant in script_dir.glob("result*"):
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
        print(f"Expected: regular file")
        print(f"Actual: {path.stat().st_mode:o} ({iso_path})")
        return False

    return True
