"""Pytest configuration and shared fixtures

No class-based fixtures, only functions.
"""

from pathlib import Path

# Type ignore for pytest - it's a test dependency
import pytest  # type: ignore


def project_root() -> Path:
    """Get the project root directory
    
    Returns:
        Path to the project root
    """
    return Path(__file__).parent.parent.absolute()


def temp_test_dir(tmp_path: Path) -> Path:
    """Get a temporary test directory
    
    Args:
        tmp_path: pytest's built-in temporary directory
        
    Returns:
        Path to temporary directory
    """
    return tmp_path
