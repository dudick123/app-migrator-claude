"""Integration tests for recursive directory scanning"""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, scan_directory


@pytest.fixture
def nested_structure(tmp_path: Path) -> Path:
    """Create a complex nested directory structure"""
    # Top level files
    (tmp_path / "top1.yaml").write_text("top: 1")
    (tmp_path / "top2.yml").write_text("top: 2")

    # First level subdirectory
    level1 = tmp_path / "level1"
    level1.mkdir()
    (level1 / "level1_app.yaml").write_text("level: 1")

    # Second level subdirectory
    level2 = level1 / "level2"
    level2.mkdir()
    (level2 / "level2_app.yml").write_text("level: 2")

    # Third level subdirectory
    level3 = level2 / "level3"
    level3.mkdir()
    (level3 / "level3_app.yaml").write_text("level: 3")

    # Hidden directory (should be skipped)
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "hidden.yaml").write_text("hidden: true")

    # Hidden directory in subdirectory (should be skipped)
    hidden_nested = level1 / ".cache"
    hidden_nested.mkdir()
    (hidden_nested / "cache.yaml").write_text("cache: true")

    return tmp_path


def test_recursive_scan_finds_all_levels(nested_structure: Path) -> None:
    """Test that recursive scan finds files at all directory levels"""
    options = ScanOptions(input_dir=nested_structure, recursive=True)
    result = scan_directory(options)

    # Should find: top1.yaml, top2.yml, level1_app.yaml, level2_app.yml, level3_app.yaml
    # Should NOT find: hidden.yaml, cache.yaml
    assert result.count == 5
    assert not result.has_errors

    # Verify files are from different depths
    depths = {len(f.relative_to(nested_structure).parts) for f in result.files}
    assert 1 in depths  # Top level files
    assert 2 in depths  # level1 files
    assert 3 in depths  # level2 files
    assert 4 in depths  # level3 files


def test_recursive_scan_skips_hidden_directories(nested_structure: Path) -> None:
    """Test that recursive scan skips hidden directories"""
    options = ScanOptions(input_dir=nested_structure, recursive=True)
    result = scan_directory(options)

    # None of the files should be from hidden directories
    for file_path in result.files:
        relative = file_path.relative_to(nested_structure.resolve())
        # Check that no part of the path starts with '.'
        assert not any(part.startswith('.') for part in relative.parts)


def test_recursive_scan_handles_symlinks(tmp_path: Path) -> None:
    """Test that recursive scan ignores symlinks to prevent infinite loops"""
    # Create a directory with files
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "app.yaml").write_text("app: true")

    # Create a symlink that would cause a cycle
    symlink = real_dir / "link_to_parent"
    try:
        symlink.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation not supported on this system")

    options = ScanOptions(input_dir=tmp_path, recursive=True)
    result = scan_directory(options)

    # Should find only the real file, not infinite files from cycle
    assert result.count == 1
    assert not result.has_errors
    assert result.files[0].name == "app.yaml"


def test_recursive_scan_empty_subdirectories(tmp_path: Path) -> None:
    """Test that recursive scan handles empty subdirectories gracefully"""
    # Create nested empty directories
    (tmp_path / "empty1" / "empty2" / "empty3").mkdir(parents=True)

    # Create one file at the top
    (tmp_path / "app.yaml").write_text("app: true")

    options = ScanOptions(input_dir=tmp_path, recursive=True)
    result = scan_directory(options)

    # Should find only the one file
    assert result.count == 1
    assert not result.has_errors
