"""Core YAML parsing and validation logic for ArgoCD manifests."""

import json
import yaml
from pathlib import Path
from typing import Any
from pydantic import ValidationError as PydanticValidationError

from parser.models import (
    ArgoCDApplication,
    MigrationOutput,
    ParseResult,
    ValidationError,
)
from parser.mapper import transform_to_migration_output


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
    with open(file_path, "r", encoding="utf-8") as f:
        # Use safe_load_all to detect multi-document YAML
        documents = list(yaml.safe_load_all(f))

    if len(documents) == 0:
        raise YAMLDocumentError(
            f"File contains 0 YAML documents. Expected exactly 1 document."
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
