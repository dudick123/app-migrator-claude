"""Unit tests for filter functions"""

from pathlib import Path

import pytest

from scanner.filters import is_hidden_directory, is_yaml_file


class TestIsYamlFile:
    """Tests for is_yaml_file function"""

    def test_yaml_extension(self) -> None:
        """Test that .yaml files are recognized"""
        assert is_yaml_file(Path("file.yaml")) is True

    def test_yml_extension(self) -> None:
        """Test that .yml files are recognized"""
        assert is_yaml_file(Path("file.yml")) is True

    def test_uppercase_yaml_extension(self) -> None:
        """Test that .YAML files are recognized (case-insensitive)"""
        assert is_yaml_file(Path("file.YAML")) is True

    def test_uppercase_yml_extension(self) -> None:
        """Test that .YML files are recognized (case-insensitive)"""
        assert is_yaml_file(Path("file.YML")) is True

    def test_non_yaml_file(self) -> None:
        """Test that non-YAML files are rejected"""
        assert is_yaml_file(Path("file.txt")) is False
        assert is_yaml_file(Path("file.json")) is False
        assert is_yaml_file(Path("file.py")) is False


class TestIsHiddenDirectory:
    """Tests for is_hidden_directory function"""

    def test_hidden_directory(self, tmp_path: Path) -> None:
        """Test that hidden directories are detected"""
        hidden_path = tmp_path / ".hidden" / "file.yaml"
        assert is_hidden_directory(hidden_path) is True

    def test_nested_hidden_directory(self, tmp_path: Path) -> None:
        """Test that nested hidden directories are detected"""
        hidden_path = tmp_path / "normal" / ".hidden" / "file.yaml"
        assert is_hidden_directory(hidden_path) is True

    def test_normal_directory(self, tmp_path: Path) -> None:
        """Test that normal directories are not marked as hidden"""
        normal_path = tmp_path / "normal" / "file.yaml"
        assert is_hidden_directory(normal_path) is False

    def test_dot_in_filename_not_hidden(self, tmp_path: Path) -> None:
        """Test that files with dots in name (but not directories) are not marked as hidden"""
        # This tests that only directory parts are checked, not the file name itself
        path_with_dot = tmp_path / "normal" / "file.config.yaml"
        assert is_hidden_directory(path_with_dot) is False
