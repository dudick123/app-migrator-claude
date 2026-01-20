"""Core YAML parsing and validation logic for ArgoCD manifests."""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from parser.mapper import transform_to_migration_output
from parser.models import (
    ArgoCDApplication,
    MigrationOutput,
    ParseResult,
    ValidationError,
)


class YAMLDocumentError(Exception):
    """Raised when YAML file has invalid document structure."""

    pass


def load_single_yaml_document(file_path: Path) -> dict[str, Any]:
    """Load and validate a single YAML document from a file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Parsed YAML document as a dictionary

    Raises:
        YAMLDocumentError: If file contains multiple documents or is empty
        yaml.YAMLError: If YAML parsing fails
        FileNotFoundError: If file doesn't exist
    """
    with open(file_path, encoding="utf-8") as f:
        # Use safe_load_all to detect multi-document YAML
        documents = list(yaml.safe_load_all(f))

    if len(documents) == 0:
        raise YAMLDocumentError(
            "File contains 0 YAML documents. Expected exactly 1 document."
        )

    if len(documents) > 1:
        raise YAMLDocumentError(
            f"File contains {len(documents)} YAML documents. "
            f"Expected exactly 1 document. Multi-document YAML files are not supported."
        )

    document = documents[0]

    if document is None:
        raise YAMLDocumentError(
            "File contains an empty YAML document. Expected a valid ArgoCD Application manifest."
        )

    if not isinstance(document, dict):
        raise YAMLDocumentError(
            f"Expected YAML document to be a mapping (dict), got {type(document).__name__}"
        )

    return document


def parse_argocd_manifest(
    file_path: Path,
    cluster_mappings: dict[str, str] | None = None,
    default_labels: dict[str, str] | None = None,
) -> MigrationOutput:
    """Parse an ArgoCD Application manifest and transform to migration output.

    Args:
        file_path: Path to the ArgoCD YAML manifest file
        cluster_mappings: Optional mapping of server URLs to cluster names
        default_labels: Optional default labels to add to output

    Returns:
        Transformed migration output

    Raises:
        YAMLDocumentError: If YAML structure is invalid
        PydanticValidationError: If manifest doesn't conform to ArgoCD schema
        FileNotFoundError: If file doesn't exist
    """
    # Load and parse YAML
    document = load_single_yaml_document(file_path)

    # Validate against ArgoCD Application schema
    app = ArgoCDApplication.model_validate(document)

    # Transform to migration output format
    output = transform_to_migration_output(app, cluster_mappings, default_labels)

    return output


def write_json_output(output: MigrationOutput, output_file: Path) -> None:
    """Write migration output to JSON file.

    Args:
        output: Migration output data
        output_file: Path where JSON file should be written

    Raises:
        OSError: If file cannot be written
    """
    # Ensure parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with proper formatting
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            output.model_dump(mode="json"),
            f,
            indent=2,
            ensure_ascii=False,
        )


def parse_and_write(
    input_file: Path,
    output_dir: Path,
    cluster_mappings: dict[str, str] | None = None,
    default_labels: dict[str, str] | None = None,
) -> ParseResult:
    """Parse ArgoCD manifest and write JSON output.

    High-level function that orchestrates parsing and writing.

    Args:
        input_file: Path to input YAML manifest
        output_dir: Directory where JSON output should be written
        cluster_mappings: Optional cluster URL to name mappings
        default_labels: Optional default labels

    Returns:
        ParseResult with status and details
    """
    try:
        # Parse the manifest
        output = parse_argocd_manifest(input_file, cluster_mappings, default_labels)

        # Determine output file name (use application name)
        output_file = output_dir / f"{output.metadata.name}.json"

        # Write JSON output
        write_json_output(output, output_file)

        return ParseResult(
            file_path=str(input_file),
            status="success",
            output_path=str(output_file),
            application_name=output.metadata.name,
        )

    except YAMLDocumentError as e:
        return ParseResult(
            file_path=str(input_file),
            status="failed",
            errors=[
                ValidationError(
                    error_type="YAML_DOCUMENT_ERROR",
                    message=str(e),
                )
            ],
        )

    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                ValidationError(
                    error_type="VALIDATION_ERROR",
                    field=field_path,
                    message=error["msg"],
                )
            )

        return ParseResult(
            file_path=str(input_file),
            status="failed",
            errors=errors,
        )

    except Exception as e:
        return ParseResult(
            file_path=str(input_file),
            status="failed",
            errors=[
                ValidationError(
                    error_type="UNEXPECTED_ERROR",
                    message=f"{type(e).__name__}: {str(e)}",
                )
            ],
        )
