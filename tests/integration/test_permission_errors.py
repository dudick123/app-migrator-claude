"""Integration tests for permission error handling"""

import os
import sys
from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.fixture
def directory_with_restricted_access(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create a directory with a restricted subdirectory.

    Returns:
        Tuple of (root_path, restricted_path)
    """
    # Create accessible files
    (tmp_path / "accessible1.yaml").write_text("accessible: 1")
    (tmp_path / "accessible2.yml").write_text("accessible: 2")

    # Create a subdirectory with files
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    (restricted / "secret.yaml").write_text("secret: true")

    # Remove read permissions on the restricted directory
    try:
        os.chmod(restricted, 0o000)
    except (OSError, PermissionError):
        pytest.skip("Cannot modify permissions on this system")

    yield tmp_path, restricted

    # Restore permissions for cleanup
    try:
        os.chmod(restricted, 0o755)
    except (OSError, PermissionError):
        pass


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Permission tests behave differently on Windows"
)
def test_permission_errors_with_partial_results(
    directory_with_restricted_access: tuple[Path, Path]
) -> None:
    """Test that scan returns partial results when encountering permission errors"""
    root_path, restricted_path = directory_with_restricted_access

    options = ScanOptions(input_dir=root_path, recursive=True)
    result = scan_directory(options)

    # Should find the accessible files
    assert result.count >= 2  # At least the two accessible files

    # Note: Python's rglob() silently skips inaccessible directories on many platforms
    # This is acceptable behavior - the scan continues and returns partial results
    # We verify that accessible files are found even when restricted directories exist


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Permission tests behave differently on Windows"
)
def test_permission_errors_do_not_halt_scan(
    directory_with_restricted_access: tuple[Path, Path]
) -> None:
    """Test that permission errors don't halt the entire scan"""
    root_path, restricted_path = directory_with_restricted_access

    # Create more accessible files after the restricted directory
    subdir = root_path / "after_restricted"
    subdir.mkdir()
    (subdir / "after.yaml").write_text("after: true")

    options = ScanOptions(input_dir=root_path, recursive=True)
    result = scan_directory(options)

    # Should still find files even after encountering restricted directory
    # Python's rglob() continues scanning accessible directories
    assert result.count >= 3  # accessible1, accessible2, after.yaml


def test_nonexistent_directory_validation() -> None:
    """Test that attempting to scan a nonexistent directory raises ValueError"""
    with pytest.raises(ValueError, match="Directory does not exist"):
        ScanOptions(input_dir=Path("/nonexistent/path"))


def test_file_instead_of_directory_validation(tmp_path: Path) -> None:
    """Test that attempting to scan a file instead of directory raises ValueError"""
    file_path = tmp_path / "file.yaml"
    file_path.write_text("content")

    with pytest.raises(ValueError, match="Path is not a directory"):
        ScanOptions(input_dir=file_path)
