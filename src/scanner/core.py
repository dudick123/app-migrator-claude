"""Core data models and scanning logic for YAML file scanner"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# Type aliases
OutputFormat = Literal["json", "human"]
VerbosityLevel = Literal["quiet", "info", "verbose"]


class ScanOptions(BaseModel):
    """Configuration for YAML file scanning operation"""

    input_dir: Path = Field(
        ...,
        description="Directory to scan for YAML files"
    )

    recursive: bool = Field(
        default=False,
        description="Whether to scan subdirectories recursively"
    )

    format: OutputFormat = Field(
        default="human",
        description="Output format: 'json' for JSON array, 'human' for formatted terminal output"
    )

    verbosity: VerbosityLevel = Field(
        default="info",
        description=(
            "Output verbosity level: 'quiet' (errors only), "
            "'info' (summary), 'verbose' (detailed)"
        ),
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('input_dir')
    @classmethod
    def validate_directory_exists(cls, v: Path) -> Path:
        """Ensure the input directory exists and is a directory"""
        if not v.exists():
            raise ValueError(f"Directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return v.resolve()  # Convert to absolute path


class ScanResult(BaseModel):
    """Result of a YAML file scanning operation"""

    files: list[Path] = Field(
        default_factory=list,
        description="List of discovered YAML file paths (absolute paths)"
    )

    errors: list[str] = Field(
        default_factory=list,
        description="List of error messages encountered during scanning (e.g., permission errors)"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def count(self) -> int:
        """Number of YAML files found"""
        return len(self.files)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_errors(self) -> bool:
        """Whether any errors were encountered during scanning"""
        return len(self.errors) > 0

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_json_array(self) -> list[str]:
        """
        Convert to simple JSON array of file path strings.
        This is the format required by FR-015 for JSON output.

        Returns:
            List of absolute file paths as strings
        """
        return [str(f) for f in self.files]


def scan_directory(options: ScanOptions) -> ScanResult:
    """
    Scan directory for YAML files according to options.

    Args:
        options: Validated scan configuration

    Returns:
        ScanResult containing discovered files and any errors
    """
    files: list[Path] = []
    errors: list[str] = []

    try:
        # Determine which glob pattern to use based on recursive flag
        patterns = ["*.yaml", "*.yml", "*.YAML", "*.YML"]

        for pattern in patterns:
            try:
                if options.recursive:
                    # Recursive glob (rglob doesn't follow symlinks by default in Python 3.10+)
                    iterator = options.input_dir.rglob(pattern)
                else:
                    # Non-recursive glob
                    iterator = options.input_dir.glob(pattern)

                for path in iterator:
                    try:
                        # Skip hidden directories
                        if _is_hidden(path):
                            continue

                        # Resolve to absolute path and deduplicate
                        resolved_path = path.resolve()
                        if resolved_path not in files:
                            files.append(resolved_path)
                    except PermissionError:
                        errors.append(f"Permission denied: {path}")
                    except Exception as e:
                        errors.append(f"Error accessing {path}: {str(e)}")
            except PermissionError:
                errors.append(f"Permission denied accessing directory: {options.input_dir}")
            except Exception as e:
                errors.append(f"Error scanning with pattern {pattern}: {str(e)}")
    except Exception as e:
        errors.append(f"Unexpected error during scan: {str(e)}")

    return ScanResult(files=sorted(files), errors=errors)


def _is_hidden(path: Path) -> bool:
    """
    Check if any part of the path is a hidden directory (starts with '.')

    Args:
        path: Path to check

    Returns:
        True if any directory component starts with '.', False otherwise
    """
    return any(part.startswith('.') for part in path.parts if part != '.')
