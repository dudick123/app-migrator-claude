"""Validation helper functions for ArgoCD manifests."""

from typing import Any


def is_argocd_application(document: dict[str, Any]) -> bool:
    """Check if a YAML document is an ArgoCD Application manifest.

    Args:
        document: Parsed YAML document

    Returns:
        True if document has correct apiVersion and kind
    """
    return (
        document.get("apiVersion") == "argoproj.io/v1alpha1"
        and document.get("kind") == "Application"
    )


def get_validation_error_summary(errors: list[dict[str, Any]]) -> str:
    """Format Pydantic validation errors into a human-readable summary.

    Args:
        errors: List of Pydantic error dictionaries

    Returns:
        Formatted error summary string
    """
    if not errors:
        return "No validation errors"

    summaries = []
    for error in errors:
        field_path = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        summaries.append(f"{field_path}: {msg}")

    return "; ".join(summaries)


def validate_required_fields(document: dict[str, Any]) -> list[str]:
    """Check for presence of required fields in ArgoCD Application manifest.

    Args:
        document: Parsed YAML document

    Returns:
        List of missing required field paths
    """
    missing = []

    # Top-level required fields
    if "apiVersion" not in document:
        missing.append("apiVersion")
    if "kind" not in document:
        missing.append("kind")
    if "metadata" not in document:
        missing.append("metadata")
    else:
        metadata = document["metadata"]
        if "name" not in metadata or not metadata.get("name"):
            missing.append("metadata.name")

    if "spec" not in document:
        missing.append("spec")
    else:
        spec = document["spec"]
        if "source" not in spec:
            missing.append("spec.source")
        else:
            source = spec["source"]
            if "repoURL" not in source or not source.get("repoURL"):
                missing.append("spec.source.repoURL")
            # Either path or chart must be present
            if "path" not in source and "chart" not in source:
                missing.append("spec.source.path or spec.source.chart")

        if "destination" not in spec:
            missing.append("spec.destination")
        else:
            dest = spec["destination"]
            if "namespace" not in dest or not dest.get("namespace"):
                missing.append("spec.destination.namespace")
            # Either server or name must be present
            if "server" not in dest and "name" not in dest:
                missing.append("spec.destination.server or spec.destination.name")

    return missing


def validate_empty_null_fields(document: dict[str, Any]) -> list[str]:
    """Check for empty or null values in required fields.

    Args:
        document: Parsed YAML document

    Returns:
        List of field paths with empty/null values
    """
    empty_fields = []

    # Check metadata.name
    if "metadata" in document:
        name = document["metadata"].get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            empty_fields.append("metadata.name")

    # Check spec fields
    if "spec" in document:
        spec = document["spec"]

        if "source" in spec:
            source = spec["source"]
            repo_url = source.get("repoURL")
            if repo_url is not None and (not isinstance(repo_url, str) or not repo_url.strip()):
                empty_fields.append("spec.source.repoURL")

        if "destination" in spec:
            dest = spec["destination"]
            namespace = dest.get("namespace")
            if namespace is not None and (not isinstance(namespace, str) or not namespace.strip()):
                empty_fields.append("spec.destination.namespace")

    return empty_fields
