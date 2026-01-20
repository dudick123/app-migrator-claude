# Data Model: ArgoCD YAML Parser

**Feature**: 002-argocd-yaml-parser
**Date**: 2026-01-18
**Status**: Design Complete

## Overview

This document defines the data models used in the ArgoCD YAML Parser (Pipeline Stage 2). All models use Pydantic v2 for type-safe validation with strict mode enabled.

---

## Model Hierarchy

```
ArgoCDApplication (input validation)
    ├── ArgoCDMetadata
    ├── ArgoCDSpec
    │   ├── ArgoCDSource
    │   ├── ArgoCDDestination
    │   └── ArgoCDSyncPolicy (optional)

MigrationOutput (transformation result)
    ├── OutputMetadata
    ├── OutputSource
    └── OutputDestination

ParseResult (processing outcome)
    ├── ArgoCD Manifest (Optional)
    └── List[ValidationError]

BatchSummary (batch processing summary)
    └── List[ParseResult]
```

---

## 1. Input Models (ArgoCD Application Manifest)

### 1.1 ArgoCDMetadata

Represents the `metadata` section of an ArgoCD Application manifest.

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `name` | `RequiredStr` | Yes | - | Non-empty, trimmed |
| `namespace` | `RequiredStr` | Yes | `"argocd"` | Non-empty, trimmed |
| `labels` | `Optional[Dict[str, str]]` | No | `None` | Key-value pairs |
| `annotations` | `Optional[Dict[str, str]]` | No | `None` | Key-value pairs |

**Pydantic Model**:
```python
from typing import Optional, Dict, Annotated
from pydantic import BaseModel, AfterValidator

def non_empty_str(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("Field cannot be empty or whitespace-only")
    return value.strip()

RequiredStr = Annotated[str, AfterValidator(non_empty_str)]

class ArgoCDMetadata(BaseModel):
    """ArgoCD Application metadata section."""
    name: RequiredStr
    namespace: RequiredStr = "argocd"
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
```

**Validation Rules**:
- `name` and `namespace` cannot be empty strings or whitespace-only
- Whitespace is automatically trimmed from string fields
- `labels` and `annotations` must be flat string dictionaries (no nested objects)

---

### 1.2 ArgoCDDestination

Represents the `spec.destination` section defining where the application will be deployed.

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `server` | `Optional[RequiredStr]` | Conditional* | `None` | Valid if `name` is None |
| `name` | `Optional[RequiredStr]` | Conditional* | `None` | Valid if `server` is None |
| `namespace` | `RequiredStr` | Yes | - | Non-empty, trimmed |

*Either `server` or `name` must be provided, but not both.

**Pydantic Model**:
```python
from pydantic import BaseModel, model_validator

class ArgoCDDestination(BaseModel):
    """ArgoCD Application destination section."""
    server: Optional[RequiredStr] = None
    name: Optional[RequiredStr] = None
    namespace: RequiredStr

    @model_validator(mode='after')
    def validate_server_or_name(self) -> 'ArgoCDDestination':
        """Ensure exactly one of 'server' or 'name' is provided."""
        if self.server is None and self.name is None:
            raise ValueError(
                "Either 'server' or 'name' must be specified in destination"
            )
        if self.server is not None and self.name is not None:
            raise ValueError(
                "Only one of 'server' or 'name' can be specified in destination, "
                "not both"
            )
        return self

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
```

**Validation Rules**:
- Exactly one of `server` OR `name` must be provided (mutually exclusive)
- `namespace` is always required and cannot be empty
- `server` typically contains Kubernetes API server URL (e.g., `"https://kubernetes.default.svc"`)
- `name` is a cluster name reference defined in ArgoCD cluster secrets

---

### 1.3 ArgoCDSource

Represents the `spec.source` section defining the application's manifest source.

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `repoURL` | `RequiredStr` | Yes | - | Valid Git/Helm URL |
| `targetRevision` | `str` | No | `"HEAD"` | Any string (branch/tag/commit) |
| `path` | `Optional[str]` | Conditional** | `None` | If provided, non-empty |
| `chart` | `Optional[str]` | Conditional** | `None` | If provided, non-empty |

**Either `path` (for Git) or `chart` (for Helm) must be provided.

**Pydantic Model**:
```python
from pydantic import BaseModel, field_validator, model_validator

class ArgoCDSource(BaseModel):
    """ArgoCD Application source section."""
    repoURL: RequiredStr
    targetRevision: str = "HEAD"
    path: Optional[str] = None
    chart: Optional[str] = None

    @field_validator('path', 'chart', mode='after')
    @classmethod
    def validate_optional_paths(cls, value: Optional[str]) -> Optional[str]:
        """If path/chart is provided, it must not be empty."""
        if value is not None and not value.strip():
            raise ValueError("If provided, path/chart cannot be empty or whitespace-only")
        return value.strip() if value else None

    @model_validator(mode='after')
    def validate_path_or_chart(self) -> 'ArgoCDSource':
        """Ensure at least one of 'path' or 'chart' is provided."""
        if self.path is None and self.chart is None:
            raise ValueError(
                "Either 'path' (for Git) or 'chart' (for Helm) must be specified "
                "in source"
            )
        return self

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
```

**Validation Rules**:
- `repoURL` is always required (Git or Helm repository URL)
- `targetRevision` defaults to `"HEAD"` if not provided
- At least one of `path` OR `chart` must be specified
- If `path` or `chart` is provided, it cannot be an empty string

---

### 1.4 ArgoCDSyncPolicy

Represents the optional `spec.syncPolicy` section.

**Fields**:
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `automated` | `Optional[Dict[str, bool]]` | No | `None` |
| `syncOptions` | `Optional[List[str]]` | No | `None` |
| `retry` | `Optional[Dict[str, Any]]` | No | `None` |

**Pydantic Model**:
```python
from typing import Any, List

class ArgoCDSyncPolicy(BaseModel):
    """ArgoCD Application sync policy (optional)."""
    automated: Optional[Dict[str, bool]] = None
    syncOptions: Optional[List[str]] = None
    retry: Optional[Dict[str, Any]] = None

    model_config = {
        "extra": "allow",  # Allow additional fields (ArgoCD may add new sync options)
        "validate_assignment": True,
    }
```

**Notes**:
- This is an optional field (spec.syncPolicy may be absent)
- Structure is flexible to accommodate ArgoCD's evolving sync policy options
- Exact validation of nested fields is not enforced (out of scope per FR-004)

---

### 1.5 ArgoCDSpec

Represents the `spec` section of an ArgoCD Application.

**Fields**:
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `project` | `str` | No | `"default"` |
| `source` | `ArgoCDSource` | Yes*** | - |
| `destination` | `ArgoCDDestination` | Yes | - |
| `syncPolicy` | `Optional[ArgoCDSyncPolicy]` | No | `None` |
| `ignoreDifferences` | `Optional[List[Dict[str, Any]]]` | No | `None` |
| `info` | `Optional[List[Dict[str, str]]]` | No | `None` |

***Note: `spec.source` or `spec.sources` (not modeled yet - out of scope for v1).

**Pydantic Model**:
```python
class ArgoCDSpec(BaseModel):
    """ArgoCD Application spec section."""
    project: str = "default"
    source: ArgoCDSource
    destination: ArgoCDDestination
    syncPolicy: Optional[ArgoCDSyncPolicy] = None
    ignoreDifferences: Optional[List[Dict[str, Any]]] = None
    info: Optional[List[Dict[str, str]]] = None

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
```

**Validation Rules**:
- `project` defaults to `"default"` if not provided or empty
- `source` and `destination` are always required
- `syncPolicy`, `ignoreDifferences`, and `info` are optional

---

### 1.6 ArgoCDApplication

Top-level model representing a complete ArgoCD Application manifest.

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `apiVersion` | `RequiredStr` | Yes | - | Must be `"argoproj.io/v1alpha1"` |
| `kind` | `RequiredStr` | Yes | - | Must be `"Application"` |
| `metadata` | `ArgoCDMetadata` | Yes | - | Valid metadata object |
| `spec` | `ArgoCDSpec` | Yes | - | Valid spec object |

**Pydantic Model**:
```python
class ArgoCDApplication(BaseModel):
    """Complete ArgoCD Application manifest."""
    apiVersion: RequiredStr
    kind: RequiredStr
    metadata: ArgoCDMetadata
    spec: ArgoCDSpec

    @field_validator('apiVersion', mode='after')
    @classmethod
    def validate_api_version(cls, value: str) -> str:
        """Ensure apiVersion is v1alpha1."""
        if value != "argoproj.io/v1alpha1":
            raise ValueError(
                f"Invalid apiVersion '{value}'. "
                f"Expected 'argoproj.io/v1alpha1'"
            )
        return value

    @field_validator('kind', mode='after')
    @classmethod
    def validate_kind(cls, value: str) -> str:
        """Ensure kind is Application."""
        if value != "Application":
            raise ValueError(
                f"Invalid kind '{value}'. "
                f"Expected 'Application'"
            )
        return value

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }
```

**Validation Rules**:
- `apiVersion` must exactly match `"argoproj.io/v1alpha1"`
- `kind` must exactly match `"Application"`
- All required nested objects (metadata, spec) are validated recursively

---

## 2. Output Models (Transformed JSON)

### 2.1 OutputMetadata

Represents transformed metadata for migration JSON output.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `name` | `RequiredStr` | Yes | - | From metadata.name |
| `annotations` | `Dict[str, str]` | No | `{}` | Keys normalized (remove namespace prefix, camelCase) |
| `labels` | `Dict[str, str]` | No | `{}` | May include defaults from config |

**Pydantic Model**:
```python
class OutputMetadata(BaseModel):
    """Transformed metadata for migration output."""
    name: RequiredStr
    annotations: Dict[str, str] = {}
    labels: Dict[str, str] = {}

    model_config = {
        "str_strip_whitespace": True,
    }
```

**Transformation Logic**:
- Annotation keys are normalized: `argocd.argoproj.io/sync-wave` → `syncWave`
- Labels may include defaults from external config (e.g., `environment: "dev"`)

---

### 2.2 OutputSource

Represents transformed source configuration.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `repoURL` | `RequiredStr` | Yes | - | From spec.source.repoURL |
| `revision` | `str` | Yes | `"HEAD"` | From spec.source.targetRevision (renamed) |
| `manifestPath` | `Optional[str]` | No | `None` | From spec.source.path (renamed) |
| `directory` | `Optional[Dict[str, Any]]` | No | `{"recurse": true}` | Default directory config |

**Pydantic Model**:
```python
class OutputSource(BaseModel):
    """Transformed source for migration output."""
    repoURL: RequiredStr
    revision: str = "HEAD"
    manifestPath: Optional[str] = None
    directory: Optional[Dict[str, Any]] = None

    model_config = {
        "str_strip_whitespace": True,
    }

    @model_validator(mode='after')
    def set_default_directory(self) -> 'OutputSource':
        """Set default directory configuration if manifestPath is provided."""
        if self.manifestPath and self.directory is None:
            self.directory = {"recurse": True}
        return self
```

**Transformation Logic**:
- `targetRevision` → `revision` (field renamed)
- `path` → `manifestPath` (field renamed)
- `directory.recurse` defaults to `true` if manifestPath is present

---

### 2.3 OutputDestination

Represents transformed destination configuration.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `clusterName` | `RequiredStr` | Yes | - | Mapped from server URL or name |
| `namespace` | `RequiredStr` | Yes | - | From spec.destination.namespace |

**Pydantic Model**:
```python
class OutputDestination(BaseModel):
    """Transformed destination for migration output."""
    clusterName: RequiredStr
    namespace: RequiredStr

    model_config = {
        "str_strip_whitespace": True,
    }
```

**Transformation Logic**:
- `server` URL → `clusterName` using cluster mapping config
- If `name` field is used, copy directly to `clusterName`
- Example mapping: `"https://kubernetes.default.svc"` → `"prod-cluster"`

---

### 2.4 MigrationOutput

Top-level model for the transformed JSON output.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `metadata` | `OutputMetadata` | Yes | - | Transformed metadata |
| `project` | `str` | Yes | `"default"` | From spec.project |
| `source` | `OutputSource` | Yes | - | Transformed source |
| `destination` | `OutputDestination` | Yes | - | Transformed destination |
| `enableSyncPolicy` | `bool` | Yes | `False` | Computed from syncPolicy presence |

**Pydantic Model**:
```python
class MigrationOutput(BaseModel):
    """Complete transformed migration output."""
    metadata: OutputMetadata
    project: str = "default"
    source: OutputSource
    destination: OutputDestination
    enableSyncPolicy: bool = False

    model_config = {
        "str_strip_whitespace": True,
    }
```

**Transformation Logic**:
- `enableSyncPolicy` is `True` if `spec.syncPolicy` is not None, else `False`
- All nested objects are transformed according to their respective models

---

## 3. Processing Models

### 3.1 ValidationError

Represents a validation error encountered during parsing.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `error_type` | `str` | Yes | - | Error category (e.g., "MISSING_REQUIRED_FIELD") |
| `field_path` | `str` | Yes | - | JSON path to field (e.g., "spec.source.repoURL") |
| `message` | `str` | Yes | - | Human-readable error description |
| `line_number` | `Optional[int]` | No | `None` | YAML line number (if available) |

**Python Dataclass**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationError:
    """Represents a validation error during parsing."""
    error_type: str
    field_path: str
    message: str
    line_number: Optional[int] = None

    def __str__(self) -> str:
        """Format error for display."""
        location = f" at line {self.line_number}" if self.line_number else ""
        return f"{self.field_path}: {self.message}{location}"
```

**Error Types**:
- `MISSING_REQUIRED_FIELD`: Required field is absent
- `EMPTY_REQUIRED_FIELD`: Required field has empty/null value
- `INVALID_VALUE`: Field value doesn't match expected format
- `MULTI_DOCUMENT_YAML`: File contains multiple YAML documents
- `INVALID_API_VERSION`: apiVersion is not v1alpha1
- `INVALID_KIND`: kind is not Application
- `YAML_SYNTAX_ERROR`: Malformed YAML syntax

---

### 3.2 ParseResult

Represents the outcome of parsing a single YAML file.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `success` | `bool` | Yes | - | True if parsing succeeded |
| `source_file` | `Path` | Yes | - | Path to source YAML file |
| `manifest` | `Optional[ArgoCDApplication]` | No | `None` | Parsed manifest (if successful) |
| `errors` | `List[ValidationError]` | No | `[]` | List of validation errors |

**Python Dataclass**:
```python
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path

@dataclass
class ParseResult:
    """Result of parsing a single ArgoCD manifest file."""
    success: bool
    source_file: Path
    manifest: Optional[ArgoCDApplication] = None
    errors: List[ValidationError] = field(default_factory=list)

    def __str__(self) -> str:
        """Format result for display."""
        if self.success:
            app_name = self.manifest.metadata.name if self.manifest else "unknown"
            return f"✓ {self.source_file.name}: {app_name}"
        else:
            error_count = len(self.errors)
            return f"✗ {self.source_file.name}: {error_count} error(s)"
```

**Usage**:
- Single file parsing returns one `ParseResult`
- Batch processing returns list of `ParseResult` objects

---

### 3.3 BatchSummary

Aggregates results from batch processing multiple files.

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `total_files` | `int` | Yes | - | Total files processed |
| `successful` | `int` | Yes | - | Successfully parsed files |
| `failed` | `int` | Yes | - | Failed validations |
| `results` | `List[ParseResult]` | Yes | - | Individual file results |

**Python Dataclass**:
```python
@dataclass
class BatchSummary:
    """Summary of batch processing results."""
    total_files: int
    successful: int
    failed: int
    results: List[ParseResult]

    def success_rate(self) -> float:
        """Calculate success percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100

    def __str__(self) -> str:
        """Format summary for display."""
        success_pct = self.success_rate()
        return (
            f"Batch Summary:\n"
            f"  Total: {self.total_files}\n"
            f"  Successful: {self.successful}\n"
            f"  Failed: {self.failed}\n"
            f"  Success Rate: {success_pct:.1f}%"
        )
```

**Usage**:
- Generated by batch processing operations
- Includes all individual ParseResult objects for detailed review

---

## 4. Model Usage Examples

### Example 1: Validate ArgoCD Manifest

```python
import yaml
from pathlib import Path

# Load YAML
with open("app.yaml", "r") as f:
    data = yaml.safe_load(f)

# Validate with Pydantic
try:
    app = ArgoCDApplication(**data)
    print(f"Valid application: {app.metadata.name}")
except ValidationError as e:
    for error in e.errors():
        print(f"  {error['loc']}: {error['msg']}")
```

### Example 2: Transform to Migration Output

```python
def transform_to_migration_output(
    app: ArgoCDApplication,
    cluster_mapping: Dict[str, str]
) -> MigrationOutput:
    """Transform ArgoCD manifest to migration output format."""

    # Normalize annotation keys
    normalized_annotations = {}
    if app.metadata.annotations:
        for key, value in app.metadata.annotations.items():
            normalized_key = normalize_annotation_key(key)
            normalized_annotations[normalized_key] = value

    # Map cluster server to name
    cluster_name = cluster_mapping.get(
        app.spec.destination.server,
        app.spec.destination.name or "default-cluster"
    )

    return MigrationOutput(
        metadata=OutputMetadata(
            name=app.metadata.name,
            annotations=normalized_annotations,
            labels=app.metadata.labels or {}
        ),
        project=app.spec.project,
        source=OutputSource(
            repoURL=app.spec.source.repoURL,
            revision=app.spec.source.targetRevision,
            manifestPath=app.spec.source.path
        ),
        destination=OutputDestination(
            clusterName=cluster_name,
            namespace=app.spec.destination.namespace
        ),
        enableSyncPolicy=app.spec.syncPolicy is not None
    )
```

### Example 3: Batch Processing

```python
def parse_directory(directory: Path) -> BatchSummary:
    """Parse all YAML files in a directory."""
    yaml_files = list(directory.glob("*.yaml"))
    results = []

    for yaml_file in yaml_files:
        try:
            data = load_single_yaml_document(yaml_file)
            app = ArgoCDApplication(**data)
            results.append(ParseResult(
                success=True,
                source_file=yaml_file,
                manifest=app
            ))
        except Exception as e:
            results.append(ParseResult(
                success=False,
                source_file=yaml_file,
                errors=[ValidationError(
                    error_type="PARSING_ERROR",
                    field_path="root",
                    message=str(e)
                )]
            ))

    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    return BatchSummary(
        total_files=len(results),
        successful=successful,
        failed=failed,
        results=results
    )
```

---

## Summary

This data model provides:
- ✅ Type-safe input validation with Pydantic models
- ✅ Clear transformation from ArgoCD YAML to migration JSON
- ✅ Comprehensive error tracking and reporting
- ✅ Batch processing support with detailed results
- ✅ Extensibility for future ArgoCD schema versions
