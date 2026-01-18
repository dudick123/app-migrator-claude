"""Unit tests for scanner core functionality"""

from pathlib import Path

import pytest

from scanner.core import ScanOptions, ScanResult, scan_directory


@pytest.fixture
def temp_yaml_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with YAML files for testing"""
    # Create some YAML files
    (tmp_path / "file1.yaml").touch()
    (tmp_path / "file2.yml").touch()
    (tmp_path / "file3.YAML").touch()

    # Create a non-YAML file
    (tmp_path / "file4.txt").touch()

    return tmp_path


@pytest.fixture
def temp_nested_dir(tmp_path: Path) -> Path:
    """Create a nested directory structure with YAML files"""
    # Top level
    (tmp_path / "top1.yaml").touch()
    (tmp_path / "top2.yml").touch()

    # Subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "sub1.yaml").touch()
    (subdir / "sub2.yml").touch()

    # Nested subdirectory
    nested = subdir / "nested"
    nested.mkdir()
    (nested / "nested1.yaml").touch()

    # Hidden directory (should be skipped)
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "hidden.yaml").touch()

    return tmp_path


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Create an empty directory"""
    return tmp_path


class TestScanOptions:
    """Tests for ScanOptions validation"""

    def test_valid_directory(self, temp_yaml_dir: Path) -> None:
        """Test that valid directory passes validation"""
        options = ScanOptions(input_dir=temp_yaml_dir)
        assert options.input_dir == temp_yaml_dir.resolve()

    def test_nonexistent_directory_raises_error(self, tmp_path: Path) -> None:
        """Test that nonexistent directory raises ValueError"""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="Directory does not exist"):
            ScanOptions(input_dir=nonexistent)

    def test_file_instead_of_directory_raises_error(self, tmp_path: Path) -> None:
        """Test that file path raises ValueError"""
        file_path = tmp_path / "file.yaml"
        file_path.touch()

        with pytest.raises(ValueError, match="Path is not a directory"):
            ScanOptions(input_dir=file_path)

    def test_default_values(self, temp_yaml_dir: Path) -> None:
        """Test that default values are set correctly"""
        options = ScanOptions(input_dir=temp_yaml_dir)

        assert options.recursive is False
        assert options.format == "human"
        assert options.verbosity == "info"


class TestScanResult:
    """Tests for ScanResult model"""

    def test_empty_result(self) -> None:
        """Test empty scan result"""
        result = ScanResult()

        assert result.files == []
        assert result.errors == []
        assert result.count == 0
        assert result.has_errors is False

    def test_result_with_files(self, tmp_path: Path) -> None:
        """Test scan result with files"""
        files = [tmp_path / "file1.yaml", tmp_path / "file2.yml"]
        result = ScanResult(files=files)

        assert result.count == 2
        assert result.has_errors is False

    def test_result_with_errors(self, tmp_path: Path) -> None:
        """Test scan result with errors"""
        result = ScanResult(errors=["Permission denied: /restricted"])

        assert result.count == 0
        assert result.has_errors is True

    def test_to_json_array(self, tmp_path: Path) -> None:
        """Test conversion to JSON array format"""
        files = [tmp_path / "file1.yaml", tmp_path / "file2.yml"]
        result = ScanResult(files=files)

        json_array = result.to_json_array()

        assert isinstance(json_array, list)
        assert len(json_array) == 2
        assert all(isinstance(item, str) for item in json_array)
        assert str(tmp_path / "file1.yaml") in json_array
        assert str(tmp_path / "file2.yml") in json_array


class TestScanDirectory:
    """Tests for scan_directory function"""

    def test_scan_single_directory(self, temp_yaml_dir: Path) -> None:
        """Test scanning a single directory finds all YAML files"""
        options = ScanOptions(input_dir=temp_yaml_dir, recursive=False)
        result = scan_directory(options)

        assert result.count == 3  # file1.yaml, file2.yml, file3.YAML
        assert not result.has_errors
        assert all(f.suffix.lower() in ['.yaml', '.yml'] for f in result.files)

    def test_both_extensions_discovered(self, temp_yaml_dir: Path) -> None:
        """Test that both .yaml and .yml extensions are discovered"""
        options = ScanOptions(input_dir=temp_yaml_dir, recursive=False)
        result = scan_directory(options)

        yaml_files = [f for f in result.files if f.suffix.lower() == '.yaml']
        yml_files = [f for f in result.files if f.suffix.lower() == '.yml']

        assert len(yaml_files) > 0
        assert len(yml_files) > 0

    def test_empty_directory_returns_empty_list(self, empty_dir: Path) -> None:
        """Test that scanning an empty directory returns empty result"""
        options = ScanOptions(input_dir=empty_dir, recursive=False)
        result = scan_directory(options)

        assert result.count == 0
        assert result.files == []
        assert not result.has_errors

    def test_recursive_scan_multiple_depths(self, temp_nested_dir: Path) -> None:
        """Test recursive scan discovers files at multiple depths"""
        options = ScanOptions(input_dir=temp_nested_dir, recursive=True)
        result = scan_directory(options)

        # Should find: top1.yaml, top2.yml, sub1.yaml, sub2.yml, nested1.yaml
        # Should NOT find: hidden.yaml (in .hidden directory)
        assert result.count == 5
        assert not result.has_errors

    def test_non_recursive_default_only_top_level(self, temp_nested_dir: Path) -> None:
        """Test non-recursive scan only finds top-level files"""
        options = ScanOptions(input_dir=temp_nested_dir, recursive=False)
        result = scan_directory(options)

        # Should find: top1.yaml, top2.yml
        assert result.count == 2
        assert not result.has_errors

        # All files should be in the top directory
        assert all(f.parent == temp_nested_dir.resolve() for f in result.files)

    def test_recursive_ignores_symlinks(self, tmp_path: Path) -> None:
        """Test that recursive scan ignores symlinks to prevent cycles"""
        # Create a directory with a symlink cycle
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "file.yaml").touch()

        # Create a symlink that points back to parent (potential cycle)
        symlink_dir = real_dir / "link_to_parent"
        symlink_dir.symlink_to(tmp_path)

        options = ScanOptions(input_dir=tmp_path, recursive=True)
        result = scan_directory(options)

        # Should find only the real file, not infinite files from cycle
        assert result.count == 1
        assert not result.has_errors
