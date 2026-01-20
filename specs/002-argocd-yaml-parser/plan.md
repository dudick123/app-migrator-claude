# Implementation Plan: ArgoCD YAML Parser

**Branch**: `002-argocd-yaml-parser` | **Date**: 2026-01-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-argocd-yaml-parser/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement an ArgoCD Application manifest parser that extracts configuration from YAML files (v1alpha1 API) and transforms them into a standardized JSON format for migration planning. The parser validates manifests against the ArgoCD Application CRD schema, handles single-file and batch processing modes, and outputs JSON with transformed field mappings (e.g., `spec.source.targetRevision` → `source.revision`, `annotations` with key normalization like `argocd.argoproj.io/sync-wave` → `syncWave`).

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML (YAML parsing), Pydantic (data validation), Typer (CLI), Rich (terminal output), pathlib (file operations)
**Storage**: Filesystem (read YAML files, write JSON files to user-specified output directory)
**Testing**: pytest with pytest-cov for coverage, contract tests for JSON schema validation
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single project (CLI tool extending existing pipeline architecture)
**Performance Goals**: Process files <1MB in <5 seconds, batch processing up to 100 files with progress reporting
**Constraints**: <512MB memory usage, streaming for batch operations, single-document YAML only
**Scale/Scope**: Individual manifest files typically 1-50KB, batch operations up to 100 files per invocation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. CLI-First Design** | All functionality accessible via CLI | ✅ PASS | Parser invoked via `argocd-parse` command with file/directory args and `--output-dir` flag. Supports `--json` for machine-readable output. |
| **II. Test Coverage Required** | Unit, integration, and contract tests | ✅ PASS | Unit tests for YAML parsing, validation logic; integration tests for file I/O; contract tests for JSON schema validation against output format. |
| **III. Type Safety** | Strict typing with pyright/mypy | ✅ PASS | Pydantic models for ArgoCD manifest structure and JSON output schema. All functions type-annotated. Strict mode enabled in pyproject.toml. |
| **IV. Security-First** | Input validation, no secrets exposure | ✅ PASS | YAML files validated before parsing (prevents code injection via `!!python/object`). Path traversal prevented via pathlib validation. No credential handling in parser. |
| **V. Simplicity and Performance** | YAGNI, bounded memory, progress reporting | ✅ PASS | Simple field extraction and mapping. Streaming batch processing. Progress bar for operations >5 seconds. No premature optimization. |

### Architecture Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Pipeline Stage 2: Parser** | ✅ PASS | Implements Parser stage: takes YAML files (from Scanner stage 1), extracts ArgoCD Application fields, outputs structured data for Migrator stage 3. |
| **Independent Testability** | ✅ PASS | Parser module has clear input (YAML file path) and output (validated Python dict). Testable without Scanner or Migrator stages. |
| **Clear Input/Output Contract** | ✅ PASS | Input: Path to YAML file + validation rules. Output: Pydantic model (ArgocdManifest) or ValidationError with details. |
| **Composable** | ✅ PASS | Parser output feeds directly into Migrator stage (Stage 3). Can be used standalone or in pipeline. |
| **Error Isolation** | ✅ PASS | Per-file error handling in batch mode. One invalid file does not stop processing of others. Errors collected and reported in summary. |
| **Progress Reporting** | ✅ PASS | Rich progress bar for batch operations. Reports: files processed, validation failures, success count. |

**Constitution Check**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/002-argocd-yaml-parser/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── argocd-manifest-schema.json    # Input: ArgoCD Application v1alpha1 schema subset
│   └── migration-output-schema.json   # Output: Transformed JSON schema for migration tool
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── scanner/             # Stage 1: YAML file discovery (existing)
│   ├── __init__.py
│   ├── core.py
│   ├── cli.py
│   └── filters.py
├── parser/              # Stage 2: ArgoCD manifest parsing (NEW - this feature)
│   ├── __init__.py
│   ├── core.py          # Main parsing logic, YAML validation
│   ├── cli.py           # Typer CLI command: argocd-parse
│   ├── models.py        # Pydantic models for ArgoCD manifest and parsed output
│   ├── validator.py     # Manifest validation (schema, required fields, empty/null checks)
│   ├── mapper.py        # Field mapping logic (YAML paths → JSON output schema)
│   └── batch.py         # Batch processing with progress reporting
└── __init__.py

tests/
├── unit/
│   └── parser/          # NEW
│       ├── test_core.py           # YAML parsing, multi-doc detection
│       ├── test_validator.py      # Validation rules, error messages
│       ├── test_mapper.py         # Field extraction and transformation
│       └── test_batch.py          # Batch processing logic
├── integration/
│   └── parser/          # NEW
│       ├── test_cli.py            # CLI integration tests
│       ├── test_file_io.py        # File reading/writing, directory creation
│       └── test_pipeline.py       # Parser stage in full pipeline (Scanner → Parser)
└── contract/
    └── parser/          # NEW
        ├── test_output_schema.py  # JSON output validates against migration schema
        └── fixtures/
            ├── valid-manifests/   # Sample valid ArgoCD YAML files
            └── invalid-manifests/ # Sample invalid YAML files for error testing
```

**Structure Decision**: Single project structure. Parser is a new module (`src/parser/`) that integrates into the existing 4-stage pipeline architecture. Follows same organizational pattern as existing `scanner` module. Tests mirror source structure with unit/integration/contract separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - All constitution checks passed. No complexity justification needed.

---

## Phase 0: Outline & Research

**Status**: Planning
**Output**: `research.md`

### Research Questions

Based on the Technical Context, the following items require research to resolve unknowns:

1. **JSON Schema Transformation Rules**
   - **Question**: What are the exact field mappings between ArgoCD YAML and the target JSON schema?
   - **Context**: User provided example showing transformations like `spec.source.targetRevision` → `source.revision`, `metadata.annotations["argocd.argoproj.io/sync-wave"]` → `metadata.annotations.syncWave` (key normalization)
   - **Research Task**: Document all field mappings, including:
     - Direct mappings (1:1 field copies)
     - Renamed fields (targetRevision → revision)
     - Nested restructuring (spec.source.* → source.*)
     - Key normalization in annotations/labels (remove namespace prefixes, camelCase)
     - Derived/computed fields (enableSyncPolicy derived from presence of spec.syncPolicy)
     - Default values for missing optional fields

2. **ArgoCD Application v1alpha1 Schema Validation**
   - **Question**: What are the required vs optional fields in ArgoCD Application CRD v1alpha1?
   - **Context**: Need to validate manifests correctly (FR-002, FR-003, FR-004)
   - **Research Task**: Document official ArgoCD Application schema:
     - Required fields in metadata and spec
     - Optional fields and their default behaviors
     - Field data types (string, bool, object, array)
     - Nested structure validation rules

3. **YAML Multi-Document Detection**
   - **Question**: How to detect and reject multi-document YAML files using PyYAML?
   - **Context**: Clarification specifies rejection of multi-doc YAML (FR-002)
   - **Research Task**: Research PyYAML API:
     - `yaml.safe_load_all()` vs `yaml.safe_load()`
     - How to detect multiple documents without loading all
     - Error message best practices for multi-doc rejection

4. **Empty/Null Field Validation**
   - **Question**: How to distinguish between missing fields, empty strings, and null values in PyYAML?
   - **Context**: Requirement FR-006a treats empty/null as invalid for required fields
   - **Research Task**: Research YAML→Python conversion:
     - How PyYAML represents `field: ""`, `field:`, `field: null`
     - Validation approach using Pydantic validators
     - Error message formatting for empty/null violations

5. **Progress Reporting for Batch Operations**
   - **Question**: What is the Rich API for progress bars in CLI batch operations?
   - **Context**: FR-010 requires progress indication for batch operations
   - **Research Task**: Research Rich library:
     - `Progress` context manager usage
     - How to update progress per-file in batch loop
     - Integration with Typer CLI commands
     - Display format: "Processing file X of Y: filename.yaml"

### Unknowns to Resolve

- [ ] Complete field mapping specification (YAML paths → JSON schema)
- [ ] ArgoCD Application v1alpha1 required vs optional fields
- [ ] PyYAML multi-document detection implementation approach
- [ ] Pydantic validation for empty/null required fields
- [ ] Rich progress bar integration pattern for batch file processing

---

## Phase 1: Design & Contracts

**Status**: Not Started (blocked by Phase 0)
**Output**: `data-model.md`, `contracts/`, `quickstart.md`

### Data Model Preview

**Key Entities** (detailed in `data-model.md`):

1. **ArgocdManifest** (Pydantic model)
   - Represents parsed and validated ArgoCD Application YAML
   - Fields: apiVersion, kind, metadata (name, namespace, labels, annotations), spec (project, source, destination, syncPolicy, etc.)
   - Validators: required field checks, empty/null rejection, v1alpha1 API version enforcement

2. **MigrationOutput** (Pydantic model)
   - Represents transformed JSON configuration
   - Fields: metadata (name, annotations, labels), project, source (repoURL, revision, manifestPath, directory), destination (clusterName, namespace), enableSyncPolicy
   - Includes field mapping logic from ArgocdManifest

3. **ValidationError** (dataclass)
   - error_type: str (e.g., "MISSING_REQUIRED_FIELD", "MULTI_DOCUMENT_YAML", "EMPTY_REQUIRED_FIELD")
   - field_path: str (e.g., "spec.source.repoURL")
   - message: str (user-friendly error description)
   - line_number: Optional[int] (for YAML syntax errors)

4. **ParseResult** (dataclass)
   - success: bool
   - manifest: Optional[ArgocdManifest]
   - errors: List[ValidationError]
   - source_file: Path

5. **BatchSummary** (dataclass)
   - total_files: int
   - successful: int
   - failed: int
   - results: List[ParseResult]

### Contract Preview

**Contracts** (detailed schemas in `contracts/`):

1. **argocd-manifest-schema.json**
   - JSON Schema defining subset of ArgoCD Application v1alpha1 CRD
   - Used for input validation (ensures only supported fields are processed)

2. **migration-output-schema.json**
   - JSON Schema defining transformed output format
   - Example structure based on user input:
   ```json
   {
     "type": "object",
     "required": ["metadata", "project", "source", "destination"],
     "properties": {
       "metadata": {
         "type": "object",
         "required": ["name"],
         "properties": {
           "name": {"type": "string"},
           "annotations": {"type": "object"},
           "labels": {"type": "object"}
         }
       },
       "project": {"type": "string"},
       "source": {
         "type": "object",
         "required": ["repoURL", "revision"],
         "properties": {
           "repoURL": {"type": "string"},
           "revision": {"type": "string"},
           "manifestPath": {"type": "string"},
           "directory": {"type": "object"}
         }
       },
       "destination": {
         "type": "object",
         "required": ["namespace"],
         "properties": {
           "clusterName": {"type": "string"},
           "namespace": {"type": "string"}
         }
       },
       "enableSyncPolicy": {"type": "boolean"}
     }
   }
   ```

### Quickstart Preview

**CLI Usage** (detailed in `quickstart.md`):

```bash
# Single file parsing
argocd-parse --file manifests/app.yaml --output-dir ./output

# Batch processing
argocd-parse --directory ./manifests --output-dir ./output

# JSON output for automation
argocd-parse --file manifests/app.yaml --output-dir ./output --json
```

---

## Phase 2: Task Breakdown

**Status**: Not Started (blocked by Phase 1)
**Output**: `tasks.md` (created by `/speckit.tasks` command, NOT this plan)

Tasks will be generated after Phase 0 research and Phase 1 design are complete.

---

## Notes

### User Input Context

The user provided a specific example transformation:

**Input YAML**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: example-app
  annotations:
    argocd.argoproj.io/sync-wave: "40"
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    targetRevision: main
    path: ./manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
```

**Output JSON**:
```json
[{
  "metadata": {
    "name": "example-app",
    "annotations": {"syncWave": "40"},
    "labels": {"environment": "dev", "team": "platform"}
  },
  "project": "default",
  "source": {
    "repoURL": "https://github.com/org/repo.git",
    "revision": "main",
    "manifestPath": "./manifests",
    "directory": {"recurse": true}
  },
  "destination": {
    "clusterName": "prod-cluster",
    "namespace": "default"
  },
  "enableSyncPolicy": false
}]
```

**Key Observations**:
1. **Annotation key normalization**: `argocd.argoproj.io/sync-wave` → `syncWave` (remove namespace, camelCase)
2. **Field renaming**: `spec.source.targetRevision` → `source.revision`, `spec.source.path` → `source.manifestPath`
3. **Derived fields**: `labels.environment` and `labels.team` appear in output but not input (source unclear - may be from config/defaults)
4. **Default values**: `directory.recurse: true` not in input (default behavior or config?)
5. **Computed boolean**: `enableSyncPolicy: false` derived from absence of `spec.syncPolicy`
6. **Server mapping**: `destination.server: "https://kubernetes.default.svc"` → `destination.clusterName: "prod-cluster"` (requires cluster name resolution - NEEDS CLARIFICATION in research phase)

**Action**: Phase 0 research must clarify:
- Source of `labels.environment` and `labels.team` (hardcoded defaults? external config?)
- `directory.recurse` default value logic
- How to map `destination.server` URL to `clusterName` (lookup table? user config? assume in-cluster = "prod-cluster"?)

### Dependencies on Other Features

This parser (Stage 2) depends on:
- **Scanner (Stage 1)**: Existing `src/scanner/` provides file discovery. Parser can be invoked directly or receive file list from Scanner.
- **Migrator (Stage 3)**: Not yet implemented. Parser output (Pydantic models) will feed into Migrator for final JSON generation.
- **Validator (Stage 4)**: Not yet implemented. Migrator output will be validated against JSON schema.

**Integration Point**: Parser can be developed and tested independently. CLI command `argocd-parse` can be used standalone until full pipeline is implemented.
