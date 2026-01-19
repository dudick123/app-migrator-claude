"""Integration tests for single directory scanning"""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.fixture
def single_dir_with_files(tmp_path: Path) -> Path:
    """Create a single directory with various file types"""
    # Create YAML files
    (tmp_path / "app1.yaml").write_text("kind: Application")
    (tmp_path / "app2.yml").write_text("kind: Application")
    (tmp_path / "config.YAML").write_text("config: true")

    # Create non-YAML files
    (tmp_path / "readme.txt").write_text("readme")
    (tmp_path / "data.json").write_text('{"key": "value"}')

    # Create a subdirectory (should be ignored in non-recursive mode)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.yaml").write_text("nested: true")

    return tmp_path


def test_single_directory_scan_finds_only_top_level(single_dir_with_files: Path) -> None:
    """Test that single directory scan finds only top-level YAML files"""
    options = ScanOptions(input_dir=single_dir_with_files, recursive=False)
    result = scan_directory(options)

    # Should find 3 YAML files in top directory
    assert result.count == 3
    assert not result.has_errors

    # All files should be in the top directory
    assert all(f.parent == single_dir_with_files.resolve() for f in result.files)

    # Check that both .yaml and .yml extensions are found
    extensions = {f.suffix.lower() for f in result.files}
    assert ".yaml" in extensions
    assert ".yml" in extensions


def test_single_directory_scan_excludes_non_yaml(single_dir_with_files: Path) -> None:
    """Test that single directory scan excludes non-YAML files"""
    options = ScanOptions(input_dir=single_dir_with_files, recursive=False)
    result = scan_directory(options)

    # None of the results should have .txt or .json extensions
    extensions = {f.suffix.lower() for f in result.files}
    assert ".txt" not in extensions
    assert ".json" not in extensions


def test_single_directory_scan_absolute_paths(single_dir_with_files: Path) -> None:
    """Test that scan returns absolute paths"""
    options = ScanOptions(input_dir=single_dir_with_files, recursive=False)
    result = scan_directory(options)

    # All paths should be absolute
    assert all(f.is_absolute() for f in result.files)
