"""Filtering utilities for YAML file scanner"""

from pathlib import Path


def is_yaml_file(path: Path) -> bool:
    """
    Check if a file has a YAML extension (.yaml or .yml)

    Args:
        path: Path to check

    Returns:
        True if file has .yaml or .yml extension (case-insensitive), False otherwise
    """
    suffix_lower = path.suffix.lower()
    return suffix_lower in ['.yaml', '.yml']


def is_hidden_directory(path: Path) -> bool:
    """
    Check if any part of the path is a hidden directory (starts with '.')

    Args:
        path: Path to check

    Returns:
        True if any directory component starts with '.', False otherwise
    """
    return any(part.startswith('.') for part in path.parts if part != '.')
