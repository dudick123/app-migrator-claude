# Research: ArgoCD YAML Parser

**Feature**: 002-argocd-yaml-parser
**Date**: 2026-01-18
**Status**: Complete

## Overview

This document consolidates research findings for implementing an ArgoCD Application manifest parser in Python. The research resolves all unknowns identified in the Technical Context section of the implementation plan.

---

## 1. JSON Schema Transformation Rules

### Decision

Implement a custom field mapping layer (`mapper.py`) that transforms ArgoCD YAML fields to a normalized JSON schema suitable for migration planning tools.

### Mapping Specification

Based on the user-provided example, the following transformations are required:

#### Direct Field Mappings (No Transformation)
| YAML Path | JSON Path | Notes |
|-----------|-----------|-------|
| `metadata.name` | `metadata.name` | 1:1 copy |
| `spec.project` | `project` | Flatten spec.* to root level |
| `spec.source.repoURL` | `source.repoURL` | 1:1 copy, flatten spec.source.* |
| `spec.destination.namespace` | `destination.namespace` | 1:1 copy |

#### Renamed Fields
| YAML Path | JSON Path | Transformation |
|-----------|-----------|----------------|
| `spec.source.targetRevision` | `source.revision` | Rename: targetRevision → revision |
| `spec.source.path` | `source.manifestPath` | Rename: path → manifestPath |

#### Annotation/Label Key Normalization
| YAML Example | JSON Output | Transformation Rule |
|--------------|-------------|---------------------|
| `metadata.annotations["argocd.argoproj.io/sync-wave"]` | `metadata.annotations.syncWave` | Remove namespace prefix (`argocd.argoproj.io/`), convert to camelCase |
| `metadata.annotations["custom-key"]` | `metadata.annotations.customKey` | Convert dashes to camelCase |

**Normalization Algorithm**:
```python
def normalize_annotation_key(key: str) -> str:
    """
    Normalize annotation/label keys for JSON output.

    Examples:
        argocd.argoproj.io/sync-wave -> syncWave
        my-custom-key -> myCustomKey
        simple -> simple
    """
    # Remove ArgoCD namespace prefix
    if key.startswith("argocd.argoproj.io/"):
        key = key.replace("argocd.argoproj.io/", "")

    # Remove other common namespaces (optional)
    if "/" in key:
        key = key.split("/")[-1]  # Take part after last slash

    # Convert kebab-case or snake_case to camelCase
    parts = key.replace("_", "-").split("-")
    if len(parts) == 1:
        return parts[0]
    return parts[0] + "".join(word.capitalize() for word in parts[1:])
```

#### Computed/Derived Fields
| JSON Field | Derivation Logic |
|------------|------------------|
| `enableSyncPolicy` | `bool(spec.syncPolicy is not None)` - True if syncPolicy exists |
| `source.directory.recurse` | Default value: `true` (assumed based on example) |

#### Destination Server → Cluster Name Mapping

**CLARIFICATION NEEDED**: The example shows `spec.destination.server: "https://kubernetes.default.svc"` transformed to `destination.clusterName: "prod-cluster"`.

**Options**:
1. **Hardcoded mapping**: Use a lookup table for common cluster URLs
2. **External config file**: Allow users to provide a cluster mapping config
3. **Derive from URL**: Extract cluster name from URL (limited applicability)
4. **Leave as server URL**: Keep the server URL in output (simplest, no transformation)

**Recommendation**: Use external config file approach for flexibility:
```json
{
  "clusterMappings": {
    "https://kubernetes.default.svc": "prod-cluster",
    "https://k8s.staging.example.com": "staging-cluster"
  }
}
```

If no mapping found, fall back to using the server URL as-is or derive a default name like `cluster-default`.

#### Labels: environment and team

**CLARIFICATION NEEDED**: The output JSON includes `labels.environment: "dev"` and `labels.team: "platform"` which are NOT present in the input YAML.

**Options**:
1. **Default values**: Hardcode default labels if not present in input
2. **External config**: Allow users to specify default labels via config file
3. **Infer from context**: Attempt to derive from file path, namespace, or other metadata
4. **Omit if not present**: Only include labels that exist in input YAML

**Recommendation**: Use external config with sensible defaults:
```json
{
  "defaultLabels": {
    "environment": "dev",
    "team": "platform"
  }
}
```

Users can override via `--config` CLI flag. If not provided, omit these labels from output.

### Rationale

- **Flattening spec.***: Simplifies output structure, removes nested ArgoCD-specific hierarchy
- **Key normalization**: JSON doesn't support keys with special characters like `/`, camelCase is JS/JSON convention
- **Derived fields**: Computed values reduce complexity for downstream consumers
- **Config-based mapping**: Provides flexibility without hardcoding environment-specific values

### Alternatives Considered

- **1:1 YAML-to-JSON conversion**: Rejected - doesn't provide the normalized schema needed for migration tools
- **Full schema transformation library**: Rejected - YAGNI, custom logic is simpler for this specific use case
- **Hardcoded cluster/label defaults**: Rejected - not flexible for different environments

---

## 2. ArgoCD Application v1alpha1 Schema Validation

### Decision

Validate ArgoCD manifests against the v1alpha1 CRD schema with Pydantic models representing the subset of fields we support.

### Required Fields

**Top-Level**:
- `apiVersion`: Must be `"argoproj.io/v1alpha1"`
- `kind`: Must be `"Application"`

**Metadata** (all required):
- `metadata.name`: DNS-1123 subdomain (alphanumeric + `-`, max 253 chars)
- `metadata.namespace`: Recommended (default: `"argocd"` if omitted)

**Spec** (all required):
- `spec.project`: String (default: `"default"` if empty/omitted)
- `spec.source` OR `spec.sources`: Mutually exclusive, one must exist
- `spec.destination`: Object with required subfields

**Destination** (required):
- `destination.namespace`: Target namespace string
- `destination.server` OR `destination.name`: At least one must exist

**Source** (when using `spec.source`):
- `source.repoURL`: Git or Helm repository URL (required)
- `source.path` OR `source.chart`: At least one required (path for Git, chart for Helm)
- `source.targetRevision`: Optional (default: `"HEAD"`)

### Optional Fields Supported

Based on spec FR-004, extract these optional fields when present:
- `spec.syncPolicy`: Object with automated sync configuration
- `spec.ignoreDifferences`: Array of diff ignore rules
- `spec.info`: Array of key-value metadata
- `metadata.labels`: Object (key-value pairs)
- `metadata.annotations`: Object (key-value pairs)

### Data Types Reference

| Field | Type | Validation |
|-------|------|------------|
| `metadata.name` | string | Non-empty, DNS-1123 subdomain |
| `metadata.namespace` | string | Non-empty, DNS-1123 label |
| `spec.project` | string | Non-empty (empty → "default") |
| `destination.server` | string | Valid URL format |
| `destination.namespace` | string | Non-empty, DNS-1123 label |
| `source.repoURL` | string | Valid Git/Helm URL |
| `source.targetRevision` | string | Any non-empty string |
| `source.path` | string | Path string (if provided) |
| `syncPolicy` | object \| null | - |
| `labels` | object | Key-value string pairs |
| `annotations` | object | Key-value string pairs |

### Rationale

- **Subset approach**: Only validate fields we actually use (FR-003, FR-004) rather than full CRD schema
- **Pydantic models**: Type-safe validation with clear error messages
- **Mutual exclusivity**: Enforce `source` XOR `sources`, `server` XOR `name` using custom validators
- **Defaults**: Apply ArgoCD defaults (project="default", namespace="argocd") for better UX

### Alternatives Considered

- **Full CRD validation with jsonschema**: Rejected - overly complex, includes fields we don't need
- **Custom validation logic**: Rejected - Pydantic provides better error messages and type safety
- **Kubernetes client library**: Rejected - heavyweight dependency for simple YAML validation

---

## 3. PyYAML Multi-Document Detection

### Decision

Use `yaml.safe_load_all()` to detect multi-document YAML files and reject them with a clear error message.

### Implementation

```python
import yaml
from pathlib import Path
from typing import Dict, Any

class YAMLDocumentError(Exception):
    """Raised when YAML document validation fails."""
    pass

def load_single_yaml_document(file_path: Path) -> Dict[str, Any]:
    """
    Loads a YAML file and ensures it contains exactly one document.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        YAMLDocumentError: If file doesn't contain exactly one document
        yaml.YAMLError: If file contains invalid YAML syntax
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Load all documents to count them
    documents = list(yaml.safe_load_all(content))

    if len(documents) == 0:
        raise YAMLDocumentError(
            f"File {file_path.name} is empty or contains no valid YAML documents"
        )

    if len(documents) > 1:
        raise YAMLDocumentError(
            f"File {file_path.name} contains {len(documents)} YAML documents. "
            f"ArgoCD Application manifests must contain exactly 1 document. "
            f"Multi-document YAML files are not supported."
        )

    return documents[0]
```

### Rationale

- **safe_load() limitation**: Silently ignores additional documents, does NOT raise errors for multi-doc files
- **safe_load_all() approach**: Returns generator of all documents, allowing us to count and reject
- **Clear error messages**: Specify document count and explain the constraint (single document only)
- **Memory efficiency**: Generator is converted to list for counting, acceptable for small files

### Alternatives Considered

- **Rely on safe_load() to raise error**: Rejected - `safe_load()` does NOT raise errors for multi-doc YAML, it just ignores extras
- **Parse YAML looking for `---` separators**: Rejected - fragile, doesn't account for YAML syntax edge cases
- **Read first document only**: Rejected - requirement FR-002 mandates explicit rejection, not silent acceptance

---

## 4. Pydantic Empty/Null Field Validation

### Decision

Use Pydantic `AfterValidator` to create a reusable `RequiredStr` type that rejects empty strings, null values, and whitespace-only strings for required fields.

### Implementation

```python
from typing import Annotated, Optional
from pydantic import AfterValidator, BaseModel, field_validator

def non_empty_str(value: str) -> str:
    """
    Validates that a string is not empty or whitespace-only.

    Args:
        value: String to validate

    Returns:
        Trimmed string value

    Raises:
        ValueError: If string is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValueError("Field cannot be empty or contain only whitespace")
    return value.strip()

# Reusable type alias for required non-empty strings
RequiredStr = Annotated[str, AfterValidator(non_empty_str)]

class ArgoCDMetadata(BaseModel):
    """ArgoCD Application metadata with validation."""
    name: RequiredStr
    namespace: RequiredStr = "argocd"

class ArgoCDDestination(BaseModel):
    """ArgoCD Application destination with validation."""
    server: RequiredStr
    namespace: RequiredStr

class ArgoCDSource(BaseModel):
    """ArgoCD Application source with validation."""
    repoURL: RequiredStr
    targetRevision: str = "HEAD"  # Allow empty (defaults to "HEAD")
    path: Optional[str] = None
    chart: Optional[str] = None

    @field_validator('path', 'chart', mode='after')
    @classmethod
    def validate_optional_strings(cls, value: Optional[str]) -> Optional[str]:
        """If path/chart is provided, it must not be empty."""
        if value is not None and not value.strip():
            raise ValueError("If provided, field cannot be empty or whitespace-only")
        return value.strip() if value else None
```

### Validation Behavior

| YAML Value | Python Value | Pydantic Behavior | Result |
|------------|--------------|-------------------|--------|
| `name: "app"` | `"app"` | Valid | ✅ Accept |
| `name: ""` | `""` | Empty string | ❌ Reject: "Field cannot be empty" |
| `name:` (no value) | `None` | None for required field | ❌ Reject: "Field required" |
| `name: "  "` | `"  "` | Whitespace only | ❌ Reject: "Field cannot be empty" |
| `targetRevision:` (optional) | `None` | None (optional field) | ✅ Accept (uses default "HEAD") |
| `path: ""` (optional) | `""` | Empty string | ❌ Reject: "If provided, cannot be empty" |

### Rationale

- **AfterValidator**: Runs after Pydantic's type coercion, ensuring we validate the final string value
- **Whitespace trimming**: Returns `.strip()` to normalize values (remove leading/trailing whitespace)
- **Reusable type**: `RequiredStr` can be used for all required non-empty string fields
- **Optional field handling**: Use `@field_validator` for fields that are optional but must not be empty if provided
- **Clear error messages**: Specific messages explain what failed ("empty", "whitespace-only", "required")

### Alternatives Considered

- **BeforeValidator**: Rejected - runs before type coercion, complicates handling of None vs empty string
- **Custom validator class**: Rejected - `AfterValidator` provides simpler, more maintainable solution
- **Manual validation in __init__**: Rejected - Pydantic validators are more declarative and integrated

---

## 5. Rich Progress Bar Integration

### Decision

Use Rich `Progress` context manager with custom columns for file processing progress tracking in batch operations.

### Implementation

```python
from pathlib import Path
from typing import List
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.console import Console

def process_yaml_files_batch(
    yaml_files: List[Path],
    console: Console
) -> None:
    """
    Process multiple YAML files with Rich progress tracking.

    Args:
        yaml_files: List of YAML file paths to process
        console: Rich console for output
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        "•",
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        task = progress.add_task(
            "Processing YAML files",
            total=len(yaml_files)
        )

        for yaml_file in yaml_files:
            # Update description to show current file
            relative_path = yaml_file.relative_to(Path.cwd())
            progress.update(
                task,
                description=f"[bold blue]Processing {relative_path.name}"
            )

            try:
                # Process the file
                result = parse_argocd_manifest(yaml_file)

                # Log success above progress bar
                progress.console.print(
                    f"[green]✓[/green] {relative_path}: "
                    f"{result.metadata.name}"
                )

            except Exception as e:
                # Log error above progress bar
                progress.console.print(
                    f"[red]✗[/red] {relative_path}: {e}"
                )

            # Advance progress
            progress.update(task, advance=1)
```

### Display Example

```
⠹ Processing example-app.yaml ━━━━━━━━━━━━━━━╸━━━━━━━━━━ 45% • 0:00:12
✓ valid-app.yaml: my-application
✗ invalid-app.yaml: Field 'metadata.name' cannot be empty
✓ another-app.yaml: guestbook
```

### Rationale

- **Context manager**: Automatically starts/stops progress display, handles cleanup
- **Custom columns**: Tailored display with spinner, description, bar, percentage, and elapsed time
- **Dynamic descriptions**: Update task description to show current file being processed
- **progress.console.print()**: Output messages above the progress bar without disrupting it
- **Color markup**: Use Rich markup (`[green]`, `[red]`, `[bold]`) for visual feedback

### Alternatives Considered

- **track() function**: Rejected - less flexible for complex status updates and custom columns
- **Manual progress updates with print()**: Rejected - doesn't integrate with Rich terminal features
- **tqdm library**: Rejected - Rich provides better terminal integration and visual styling

---

## Summary

All research questions from Phase 0 have been resolved:

✅ **JSON Schema Transformation Rules**: Documented field mappings with annotation key normalization algorithm. Identified need for external config file for cluster mappings and default labels.

✅ **ArgoCD Application v1alpha1 Schema**: Documented required fields (apiVersion, kind, metadata.name, spec.project, spec.source/sources, spec.destination) and optional fields (syncPolicy, ignoreDifferences, info, labels, annotations). Using Pydantic models for validation.

✅ **PyYAML Multi-Document Detection**: Use `yaml.safe_load_all()` to count documents and reject files with more than one. `safe_load()` silently ignores extra documents and cannot be relied upon for detection.

✅ **Pydantic Empty/Null Validation**: Use `AfterValidator` with `RequiredStr` type alias for required fields. Validates against empty strings, null values, and whitespace-only values. Returns trimmed strings.

✅ **Rich Progress Bar Integration**: Use `Progress` context manager with custom columns (spinner, text, bar, task progress, elapsed time). Update task description per-file and use `progress.console.print()` for status messages above the bar.

---

## Next Steps

Proceed to **Phase 1: Design & Contracts**:
1. Create detailed `data-model.md` with full Pydantic model definitions
2. Generate JSON schemas in `contracts/` directory
3. Write `quickstart.md` with CLI usage examples
4. Update agent context with new technologies (PyYAML, Pydantic validators, Rich progress)
