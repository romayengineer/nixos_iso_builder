"""Integration tests for build functionality

Tests that actually run nix build and verify ISO creation.
No mocking - uses real files and processes.
"""

from pathlib import Path

import pytest

from nixos_iso_builder.iso_utils import find_iso, validate_iso_is_file
from nixos_iso_builder.nix_utils import build_iso, cleanup_result_symlinks

# Get the project root directory (two levels up from tests/integration)
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()


def cleanup_iso_files(script_dir: Path) -> None:
    """Clean up all ISO files and result symlinks

    Args:
        script_dir: Project directory containing result* symlinks
    """
    # Remove result symlinks
    for result_path in script_dir.glob("result*"):
        try:
            if result_path.is_symlink() or result_path.is_file():
                result_path.unlink()
        except Exception:
            pass


def test_build_minimal_creates_iso() -> None:
    """Test that building with minimal profile creates an ISO file

    This test:
    1. Cleans up old ISO files
    2. Runs the actual nix build
    3. Verifies a new ISO file exists
    4. Validates it's a regular file (not directory)
    """
    # Arrange: Clean up old files
    cleanup_iso_files(PROJECT_ROOT)
    iso_before = find_iso(PROJECT_ROOT)
    assert iso_before is None, "Should start with no ISO file"

    # Act: Build with minimal profile
    return_code = build_iso(PROJECT_ROOT, "minimal", PROJECT_ROOT / "build.log")

    # Assert: Build succeeded
    assert return_code == 0, "Build should succeed"

    # Assert: ISO file now exists
    iso_after = find_iso(PROJECT_ROOT)
    assert iso_after is not None, "ISO file should exist after build"

    # Assert: It's a regular file, not a directory
    assert validate_iso_is_file(iso_after), "ISO should be a regular file"

    # Assert: It's a real file with content
    iso_path = Path(iso_after)
    assert iso_path.exists(), "ISO file should exist on disk"
    assert iso_path.is_file(), "ISO should be a file"
    assert iso_path.stat().st_size > 0, "ISO should have content"


def test_build_debug_creates_iso() -> None:
    """Test that building with debug profile creates an ISO file

    This test:
    1. Cleans up old ISO files
    2. Runs nix build with debug profile
    3. Verifies ISO file exists and is valid
    """
    # Arrange: Clean up old files
    cleanup_iso_files(PROJECT_ROOT)
    iso_before = find_iso(PROJECT_ROOT)
    assert iso_before is None, "Should start with no ISO file"

    # Act: Build with debug profile
    return_code = build_iso(PROJECT_ROOT, "debug", PROJECT_ROOT / "build.log")

    # Assert: Build succeeded
    assert return_code == 0, "Build should succeed"

    # Assert: ISO file exists and is valid
    iso_after = find_iso(PROJECT_ROOT)
    assert iso_after is not None, "ISO file should exist after build"
    assert validate_iso_is_file(iso_after), "ISO should be a regular file"

    iso_path = Path(iso_after)
    assert iso_path.stat().st_size > 0, "ISO should have content"


def test_cleanup_result_symlinks_removes_old_links() -> None:
    """Test that cleanup_result_symlinks removes all result symlinks

    This test:
    1. Builds an ISO (creates result symlink)
    2. Verifies result symlink exists
    3. Calls cleanup function
    4. Verifies all result* symlinks are gone
    """
    # Arrange: Build to create result symlink
    cleanup_iso_files(PROJECT_ROOT)
    build_iso(PROJECT_ROOT, "minimal", PROJECT_ROOT / "build.log")

    # Verify result symlink exists
    result_links_before = list(PROJECT_ROOT.glob("result*"))
    assert len(result_links_before) > 0, "Should have result symlink after build"

    # Act: Clean up
    cleanup_result_symlinks(PROJECT_ROOT)

    # Assert: All result symlinks are gone
    result_links_after = list(PROJECT_ROOT.glob("result*"))
    assert len(result_links_after) == 0, "All result symlinks should be removed"


def test_find_iso_returns_none_when_no_iso_exists() -> None:
    """Test that find_iso returns None when no ISO file exists

    This test:
    1. Cleans up all ISO files
    2. Calls find_iso
    3. Verifies it returns None
    """
    # Arrange: Clean up all ISO files
    cleanup_iso_files(PROJECT_ROOT)

    # Act: Search for ISO
    iso = find_iso(PROJECT_ROOT)

    # Assert: Returns None
    assert iso is None, "find_iso should return None when no ISO exists"


def test_find_iso_finds_built_iso() -> None:
    """Test that find_iso successfully finds a built ISO

    This test:
    1. Cleans up old files
    2. Builds an ISO
    3. Calls find_iso
    4. Verifies it finds the ISO
    """
    # Arrange: Build an ISO
    cleanup_iso_files(PROJECT_ROOT)
    build_iso(PROJECT_ROOT, "minimal", PROJECT_ROOT / "build.log")

    # Act: Find the ISO
    iso = find_iso(PROJECT_ROOT)

    # Assert: ISO is found
    assert iso is not None, "find_iso should find the built ISO"
    assert Path(iso).exists(), "Found ISO should exist on disk"


def test_iso_file_is_valid_nixos_iso() -> None:
    """Test that built ISO is a valid NixOS ISO

    This test:
    1. Builds an ISO
    2. Verifies it contains 'nixos' in the filename
    3. Verifies file size is reasonable for a NixOS ISO
    """
    # Arrange: Build an ISO
    cleanup_iso_files(PROJECT_ROOT)
    build_iso(PROJECT_ROOT, "minimal", PROJECT_ROOT / "build.log")

    # Act: Find the ISO
    iso = find_iso(PROJECT_ROOT)
    assert iso is not None, "ISO should exist"

    # Assert: It's a NixOS ISO
    iso_path = Path(iso)
    assert "nixos" in iso_path.name.lower(), "ISO filename should contain 'nixos'"

    # Assert: It's a reasonable size (at least 500MB for minimal ISO)
    iso_size_mb = iso_path.stat().st_size / (1024 * 1024)
    assert iso_size_mb > 500, f"ISO should be > 500MB, got {iso_size_mb:.1f}MB"
    assert iso_size_mb < 3000, f"ISO should be < 3GB, got {iso_size_mb:.1f}MB"


def test_build_log_is_created() -> None:
    """Test that build process creates a build log

    This test:
    1. Runs a build
    2. Verifies build.log file exists
    3. Verifies log contains build output
    """
    # Arrange: Clean up
    cleanup_iso_files(PROJECT_ROOT)
    build_log = PROJECT_ROOT / "build.log"
    if build_log.exists():
        build_log.unlink()

    # Act: Build
    return_code = build_iso(PROJECT_ROOT, "minimal", build_log)

    # Assert: Build succeeded
    assert return_code == 0, "Build should succeed"

    # Assert: Log file exists
    assert build_log.exists(), "build.log should be created"

    # Assert: Log has content
    log_content = build_log.read_text()
    assert len(log_content) > 0, "build.log should have content"
    assert "nixos-minimal" in log_content, "Log should contain build output"


def test_validate_iso_is_file_rejects_directories() -> None:
    """Test that validate_iso_is_file rejects directories

    This test:
    1. Creates a test directory
    2. Calls validate_iso_is_file on it
    3. Verifies it returns False
    """
    # Arrange: Create a test directory
    test_dir = PROJECT_ROOT / ".test_iso_dir"
    test_dir.mkdir(exist_ok=True)

    try:
        # Act & Assert: Should return False for directory
        assert not validate_iso_is_file(str(test_dir)), "Should reject directories"
    finally:
        # Cleanup
        test_dir.rmdir()


def test_validate_iso_is_file_accepts_valid_iso() -> None:
    """Test that validate_iso_is_file accepts valid ISO files

    This test:
    1. Builds an ISO
    2. Finds it
    3. Calls validate_iso_is_file
    4. Verifies it returns True
    """
    # Arrange: Build an ISO
    cleanup_iso_files(PROJECT_ROOT)
    build_iso(PROJECT_ROOT, "minimal", PROJECT_ROOT / "build.log")

    # Act: Find and validate
    iso = find_iso(PROJECT_ROOT)
    assert iso is not None, "ISO should exist"

    # Assert: Validation succeeds
    assert validate_iso_is_file(iso), "validate_iso_is_file should accept valid ISO"
