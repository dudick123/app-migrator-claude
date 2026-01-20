# Implementation Tasks: ArgoCD YAML Parser

**Feature**: 002-argocd-yaml-parser
**Branch**: `002-argocd-yaml-parser`
**Date**: 2026-01-18

## Overview

This task list implements the ArgoCD YAML Parser (Pipeline Stage 2) organized by user stories from the feature specification. Each user story is independently testable and delivers incremental value.

**Total Tasks**: 45
**Parallelizable Tasks**: 28 (62%)
**User Stories**: 3 (P1, P2, P3)

---

## Implementation Strategy

### MVP Scope (Recommended First Delivery)

**User Story 1 only**: Parse Valid ArgoCD Application Manifest
- Delivers core value: Parse single YAML file to JSON
- Independently testable
- Foundation for P2 and P3 stories

### Incremental Delivery

1. **Phase 1-2**: Setup + Foundational (blocking prerequisites)
2. **Phase 3**: User Story 1 (P1) - Core parsing → **MVP Release**
3. **Phase 4**: User Story 2 (P2) - Validation & error handling
4. **Phase 5**: User Story 3 (P3) - Batch processing
5. **Phase 6**: Polish & cross-cutting concerns

### Story Dependencies

```
Setup (Phase 1) ───┐
                   │
Foundational ──────┼──→ US1 (P1) ──→ US2 (P2) ──→ US3 (P3) ──→ Polish
(Phase 2)          │      ↓             ↓             ↓
                   │   (MVP)      (Validation)   (Batch)
                   │
                   └──→ Can start in parallel after Setup complete
```

**Independent Stories**: US1, US2, US3 can be implemented in parallel after Foundational phase

---

## Phase 1: Setup & Project Initialization

**Goal**: Initialize parser module structure and dependencies

### Tasks

- [X] T001 Create parser module directory structure in src/parser/
- [X] T002 Create __init__.py files for parser module and subpackages
- [X] T003 [P] Add PyYAML dependency to pyproject.toml dependencies list
- [X] T004 [P] Add pydantic>=2.0.0 to pyproject.toml dependencies list
- [X] T005 [P] Add jsonschema to pyproject.toml dependencies for contract validation
- [X] T006 [P] Create test directory structure: tests/unit/parser/, tests/integration/parser/, tests/contract/parser/
- [X] T007 [P] Create test fixtures directory: tests/contract/parser/fixtures/
- [X] T008 Create argocd-parse CLI entry point in pyproject.toml [project.scripts]
- [X] T009 Run uv sync to install new dependencies

**Completion Criteria**: Module structure created, dependencies installed, entry points configured

---

## Phase 2: Foundational Components

**Goal**: Build core reusable components needed by all user stories

**Dependencies**: Phase 1 must be complete

### Tasks

- [X] T010 [P] Define RequiredStr type alias with AfterValidator in src/parser/models.py
- [X] T011 [P] Define non_empty_str validator function in src/parser/models.py
- [X] T012 [P] Create YAMLDocumentError exception class in src/parser/core.py
- [X] T013 [P] Create ValidationError dataclass in src/parser/models.py
- [X] T014 [P] Create ParseResult dataclass in src/parser/models.py
- [X] T015 [P] Implement load_single_yaml_document() function in src/parser/core.py
- [X] T016 Write unit test for load_single_yaml_document() with single document in tests/unit/test_parser_core.py
- [X] T017 Write unit test for multi-document detection/rejection in tests/unit/test_parser_core.py
- [X] T018 Write unit test for empty YAML file handling in tests/unit/test_parser_core.py

**Completion Criteria**: Core utilities tested and ready for use in user stories

**Parallel Opportunities**: T010-T015 can run in parallel (different functions/classes)

---

## Phase 3: User Story 1 - Parse Valid ArgoCD Application Manifest (P1)

**Story Goal**: Users can parse a single valid ArgoCD manifest YAML file and get JSON output

**Why First**: Core functionality - enables migration planning and config extraction

**Independent Test**: Provide valid ArgoCD manifest → verify correct JSON output with all fields mapped

**Dependencies**: Phase 2 (Foundational) must be complete

### Acceptance Criteria

1. Valid manifest with all standard fields → correctly extracted and mapped to JSON
2. Valid manifest with optional fields (syncPolicy, etc.) → optional fields included in output
3. Non-existent output directory → automatically created with parent directories
4. Custom/non-standard fields in manifest → silently ignored, only known fields extracted

### Implementation Tasks

#### Step 1: Pydantic Models (Input Validation)

- [X] T019 [P] [US1] Define ArgoCDMetadata model in src/parser/models.py
- [X] T020 [P] [US1] Define ArgoCDDestination model with server/name XOR validator in src/parser/models.py
- [X] T021 [P] [US1] Define ArgoCDSource model with path/chart validator in src/parser/models.py
- [X] T022 [P] [US1] Define ArgoCDSyncPolicy model in src/parser/models.py
- [X] T023 [P] [US1] Define ArgoCDSpec model in src/parser/models.py
- [X] T024 [US1] Define ArgoCDApplication model with apiVersion/kind validators in src/parser/models.py

#### Step 2: Output Models (Transformation)

- [X] T025 [P] [US1] Define OutputMetadata model in src/parser/models.py
- [X] T026 [P] [US1] Define OutputSource model with default directory config in src/parser/models.py
- [X] T027 [P] [US1] Define OutputDestination model in src/parser/models.py
- [X] T028 [US1] Define MigrationOutput model in src/parser/models.py

#### Step 3: Field Mapper

- [X] T029 [US1] Implement normalize_annotation_key() function in src/parser/mapper.py
- [X] T030 [US1] Implement transform_to_migration_output() function in src/parser/mapper.py
- [X] T031 [US1] Add cluster_mapping config parameter support to transform function in src/parser/mapper.py
- [X] T032 [US1] Add default_labels config parameter support to transform function in src/parser/mapper.py

#### Step 4: Core Parser Logic

- [X] T033 [US1] Implement parse_argocd_manifest() function in src/parser/core.py
- [X] T034 [US1] Add output directory creation logic (with parents) in src/parser/core.py
- [X] T035 [US1] Implement write_json_output() function in src/parser/core.py

#### Step 5: CLI Command

- [X] T036 [US1] Create Typer app instance in src/parser/cli.py
- [X] T037 [US1] Implement parse command with --file and --output-dir flags in src/parser/cli.py
- [X] T038 [US1] Add optional --config flag for cluster mappings in src/parser/cli.py
- [X] T039 [US1] Add success/failure console output with Rich in src/parser/cli.py

#### Step 6: Unit Tests

- [X] T040 [P] [US1] Write unit tests for ArgoCDApplication Pydantic validation in tests/unit/test_parser_mapper.py
- [X] T041 [P] [US1] Write unit tests for normalize_annotation_key() in tests/unit/test_parser_mapper.py
- [X] T042 [P] [US1] Write unit tests for transform_to_migration_output() in tests/unit/test_parser_mapper.py

#### Step 7: Integration Tests

- [X] T043 [US1] Write integration test for single file parsing with valid manifest in tests/integration/test_parser_cli.py
- [X] T044 [US1] Write integration test for output directory creation in tests/integration/test_parser_cli.py
- [X] T045 [US1] Write integration test for JSON output file content validation in tests/integration/test_parser_cli.py

#### Step 8: Contract Tests

- [ ] T046 [US1] Create sample valid ArgoCD manifests in tests/contract/parser/fixtures/valid-manifests/
- [ ] T047 [US1] Write contract test validating JSON output against migration-output-schema.json in tests/contract/parser/test_output_schema.py

**Completion Criteria for US1**:
- ✅ Parse valid manifest with all standard fields → correct JSON output
- ✅ Optional fields (syncPolicy) present → included in JSON
- ✅ Output directory doesn't exist → created automatically
- ✅ Custom fields in manifest → ignored, only standard fields extracted
- ✅ All unit/integration/contract tests passing

**Parallel Opportunities**:
- T019-T023, T025-T027: Pydantic models (different classes)
- T040-T042: Unit tests (independent test files)

---

## Phase 4: User Story 2 - Detect and Report Invalid Manifests (P2)

**Story Goal**: Users get clear, actionable error messages when providing invalid YAML files

**Why Second**: Validation is essential for usability but builds on core parsing from US1

**Independent Test**: Provide various invalid YAMLs → verify specific error messages for each failure type

**Dependencies**: US1 (P1) complete (reuses parsing infrastructure)

### Acceptance Criteria

1. Non-ArgoCD manifest → reports "not an ArgoCD Application" with clear message
2. Malformed YAML syntax → reports parse error with line/column information
3. Missing required fields → reports which specific fields are missing
4. Multi-document YAML → rejects with "multi-document not supported" message
5. Empty/null required fields → reports fields with empty/null values as invalid

### Implementation Tasks

#### Step 1: Validation Logic

- [X] T048 [P] [US2] Add apiVersion validation logic to ArgoCDApplication model in src/parser/models.py
- [X] T049 [P] [US2] Add kind validation logic to ArgoCDApplication model in src/parser/models.py
- [X] T050 [P] [US2] Implement validate_required_fields() function in src/parser/validator.py
- [X] T051 [P] [US2] Implement validate_empty_null_fields() function in src/parser/validator.py
- [X] T052 [US2] Add comprehensive error message formatting in src/parser/validator.py

#### Step 2: Error Handling in Parser

- [X] T053 [US2] Add try/except for YAML syntax errors with line number extraction in src/parser/core.py
- [X] T054 [US2] Add try/except for Pydantic ValidationError with field path extraction in src/parser/core.py
- [X] T055 [US2] Add try/except for YAMLDocumentError (multi-doc detection) in src/parser/core.py
- [X] T056 [US2] Update ParseResult to include detailed error list in src/parser/core.py

#### Step 3: CLI Error Display

- [X] T057 [US2] Add error formatting with Rich for validation failures in src/parser/cli.py
- [X] T058 [US2] Add error formatting for YAML syntax errors with line numbers in src/parser/cli.py
- [X] T059 [US2] Set appropriate exit codes (0=success, 1=validation error, 2=syntax error) in src/parser/cli.py

#### Step 4: Unit Tests

- [X] T060 [P] [US2] Write tests for missing required field detection in tests/unit/test_parser_validator.py
- [X] T061 [P] [US2] Write tests for empty string validation in tests/unit/test_parser_validator.py
- [X] T062 [P] [US2] Write tests for null value validation in tests/unit/test_parser_validator.py
- [X] T063 [P] [US2] Write tests for invalid apiVersion/kind in tests/unit/test_parser_validator.py

#### Step 5: Integration Tests

- [X] T064 [US2] Create invalid manifest fixtures in tests/fixtures/parser/invalid-manifests/
- [X] T065 [US2] Write test for non-ArgoCD manifest error message in tests/integration/test_parser_cli.py
- [X] T066 [US2] Write test for YAML syntax error with line number in tests/integration/test_parser_cli.py
- [X] T067 [US2] Write test for missing required field error in tests/integration/test_parser_cli.py
- [X] T068 [US2] Write test for empty/null field error in tests/integration/test_parser_cli.py

**Completion Criteria for US2**:
- ✅ Non-ArgoCD YAML → clear "not an Application" message
- ✅ Malformed YAML → syntax error with line/column number
- ✅ Missing required fields → lists specific missing fields
- ✅ Multi-document YAML → "not supported" error message
- ✅ Empty/null required fields → identifies problematic fields
- ✅ All validation tests passing

**Parallel Opportunities**:
- T048-T051: Validation functions (independent)
- T060-T063: Unit tests (different test cases)

---

## Phase 5: User Story 3 - Batch Process Multiple Manifests (P3)

**Story Goal**: Users can process entire directories of manifests with progress reporting and summary

**Why Third**: Batch processing is a convenience feature that builds on single-file parsing

**Independent Test**: Provide directory with mix of valid/invalid manifests → all processed, summary report generated

**Dependencies**: US1 (P1) and US2 (P2) complete (reuses parsing + validation)

### Acceptance Criteria

1. Directory with multiple manifests → all files processed, individual JSON outputs generated
2. Mix of valid/invalid files → summary shows successful/failed counts with details
3. Invalid file in batch → doesn't stop processing of other files
4. Progress reporting → shows current file being processed for operations >5 seconds

### Implementation Tasks

#### Step 1: Batch Processing Logic

- [ ] T069 [US3] Create BatchSummary dataclass in src/parser/models.py
- [ ] T070 [US3] Implement find_yaml_files() function to discover *.yaml and *.yml in src/parser/batch.py
- [ ] T071 [US3] Implement process_files_batch() function with error isolation in src/parser/batch.py
- [ ] T072 [US3] Add per-file error handling (continue on failure) in src/parser/batch.py

#### Step 2: Progress Reporting

- [ ] T073 [US3] Add Rich Progress context manager to batch processing in src/parser/batch.py
- [ ] T074 [US3] Configure custom progress columns (spinner, bar, elapsed time) in src/parser/batch.py
- [ ] T075 [US3] Update progress task description per-file in src/parser/batch.py
- [ ] T076 [US3] Add per-file success/failure messages above progress bar in src/parser/batch.py

#### Step 3: Summary Reporting

- [ ] T077 [US3] Implement format_batch_summary() function in src/parser/batch.py
- [ ] T078 [US3] Add success rate calculation to BatchSummary in src/parser/batch.py
- [ ] T079 [US3] Add color-coded summary output (green/red/yellow) in src/parser/batch.py

#### Step 4: CLI Integration

- [ ] T080 [US3] Add --directory flag to parse command in src/parser/cli.py
- [ ] T081 [US3] Add mutual exclusion between --file and --directory flags in src/parser/cli.py
- [ ] T082 [US3] Add --quiet flag to suppress progress output in src/parser/cli.py
- [ ] T083 [US3] Add --json flag for machine-readable batch summary in src/parser/cli.py

#### Step 5: Unit Tests

- [ ] T084 [P] [US3] Write tests for find_yaml_files() recursive discovery in tests/unit/parser/test_batch.py
- [ ] T085 [P] [US3] Write tests for error isolation (one failure doesn't stop batch) in tests/unit/parser/test_batch.py
- [ ] T086 [P] [US3] Write tests for BatchSummary calculation in tests/unit/parser/test_batch.py

#### Step 6: Integration Tests

- [ ] T087 [US3] Create test directory with mix of valid/invalid manifests in tests/integration/parser/
- [ ] T088 [US3] Write test for batch processing with all valid files in tests/integration/parser/test_cli.py
- [ ] T089 [US3] Write test for batch processing with mixed valid/invalid files in tests/integration/parser/test_cli.py
- [ ] T090 [US3] Write test for batch summary report format in tests/integration/parser/test_cli.py
- [ ] T091 [US3] Write test for --json output format in tests/integration/parser/test_cli.py

**Completion Criteria for US3**:
- ✅ Directory scanning → finds all .yaml/.yml files recursively
- ✅ Batch processing → all files processed independently
- ✅ Error isolation → one invalid file doesn't stop processing
- ✅ Progress bar → shows current file and completion percentage
- ✅ Summary report → shows total/successful/failed/skipped counts
- ✅ --json flag → outputs machine-readable summary
- ✅ All batch processing tests passing

**Parallel Opportunities**:
- T084-T086: Unit tests (independent test files)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Documentation, type checking, linting, and final integration

**Dependencies**: All user stories (US1, US2, US3) complete

### Tasks

#### Documentation

- [ ] T092 [P] Add docstrings to all public functions in src/parser/core.py
- [ ] T093 [P] Add docstrings to all public functions in src/parser/mapper.py
- [ ] T094 [P] Add docstrings to all Pydantic models in src/parser/models.py
- [ ] T095 [P] Add docstrings to CLI commands in src/parser/cli.py
- [ ] T096 Update README.md with argocd-parse CLI usage examples

#### Type Checking & Linting

- [ ] T097 Run mypy --strict on src/parser/ and fix all type errors
- [ ] T098 Run ruff check src/parser/ and fix all linting issues
- [ ] T099 Run pytest with coverage and ensure >90% coverage for src/parser/

#### Integration with Pipeline

- [ ] T100 Write pipeline integration test (Scanner → Parser) in tests/integration/parser/test_pipeline.py
- [ ] T101 Update pyproject.toml to include parser package in wheel build
- [ ] T102 Test argocd-parse CLI command after install (smoke test)

#### Final Validation

- [ ] T103 Run full test suite (unit + integration + contract) and verify all passing
- [ ] T104 Validate JSON schema compliance for all output files in contract tests
- [ ] T105 Performance test: Parse 100 files in <30 seconds (batch processing)

**Completion Criteria**:
- ✅ All functions have type annotations and docstrings
- ✅ mypy --strict passes with no errors
- ✅ ruff check passes with no violations
- ✅ Test coverage >90% for parser module
- ✅ CLI command works after installation
- ✅ Performance targets met (<5s per file, <30s for 100 files)

**Parallel Opportunities**:
- T092-T095: Documentation (different files)
- T097-T099: Can run in parallel (independent checks)

---

## Task Summary by Phase

| Phase | Task Range | Count | Story | Description |
|-------|------------|-------|-------|-------------|
| 1 | T001-T009 | 9 | Setup | Project initialization |
| 2 | T010-T018 | 9 | Foundation | Core reusable components |
| 3 | T019-T047 | 29 | US1 (P1) | Parse valid manifests |
| 4 | T048-T068 | 21 | US2 (P2) | Validation & error handling |
| 5 | T069-T091 | 23 | US3 (P3) | Batch processing |
| 6 | T092-T105 | 14 | Polish | Documentation & integration |
| **Total** | **T001-T105** | **105** | | |

**Note**: Task counts include all implementation, testing, and documentation tasks

---

## Parallel Execution Examples

### Phase 1 (Setup) - After T002 Complete

```bash
# Can run in parallel (different files)
T003: Add PyYAML to pyproject.toml
T004: Add pydantic to pyproject.toml
T005: Add jsonschema to pyproject.toml
T006: Create test directories
T007: Create fixtures directory
```

### Phase 2 (Foundational) - All Parallel After Directory Setup

```bash
# Can run in parallel (different functions/classes)
T010: Define RequiredStr type
T011: Define non_empty_str validator
T012: Create YAMLDocumentError exception
T013: Create ValidationError dataclass
T014: Create ParseResult dataclass
T015: Implement load_single_yaml_document()
```

### Phase 3 (US1) - Pydantic Models

```bash
# Can run in parallel (independent models)
T019: ArgoCDMetadata model
T020: ArgoCDDestination model
T021: ArgoCDSource model
T022: ArgoCDSyncPolicy model
T023: ArgoCDSpec model

T025: OutputMetadata model
T026: OutputSource model
T027: OutputDestination model
```

### Phase 3 (US1) - Unit Tests

```bash
# Can run in parallel (different test files)
T040: Test ArgoCDApplication validation
T041: Test normalize_annotation_key()
T042: Test transform_to_migration_output()
```

### Phase 4 (US2) - Validation Functions

```bash
# Can run in parallel (independent validators)
T048: Add apiVersion validation
T049: Add kind validation
T050: Implement validate_required_fields()
T051: Implement validate_empty_null_fields()
```

### Phase 6 (Polish) - Documentation

```bash
# Can run in parallel (different files)
T092: Docstrings for core.py
T093: Docstrings for mapper.py
T094: Docstrings for models.py
T095: Docstrings for cli.py
```

---

## Independent Testing Criteria

### User Story 1 (P1) - Parse Valid Manifest

**Test Command**:
```bash
# Create test manifest
cat > test-app.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-app
  annotations:
    argocd.argoproj.io/sync-wave: "10"
spec:
  project: default
  source:
    repoURL: https://github.com/test/repo.git
    targetRevision: main
    path: ./manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
EOF

# Run parser
argocd-parse --file test-app.yaml --output-dir ./output

# Verify output
ls ./output/test-app.json
jq . ./output/test-app.json
```

**Expected Behavior**:
- JSON file created in ./output/
- Contains all mapped fields (metadata, project, source, destination)
- Annotations normalized (syncWave, not argocd.argoproj.io/sync-wave)
- enableSyncPolicy = false (no syncPolicy in source)

### User Story 2 (P2) - Invalid Manifest Detection

**Test Command**:
```bash
# Missing required field
cat > invalid-app.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: invalid-app
spec:
  project: default
  destination:
    server: https://kubernetes.default.svc
    namespace: default
EOF

# Run parser (should fail)
argocd-parse --file invalid-app.yaml --output-dir ./output

# Multi-document test
cat > multi-doc.yaml <<EOF
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app2
EOF

argocd-parse --file multi-doc.yaml --output-dir ./output
```

**Expected Behavior**:
- First test: Error message "spec.source: Field required"
- Second test: Error message "File contains 2 YAML documents. Expected exactly 1."
- Exit code non-zero
- No JSON output created

### User Story 3 (P3) - Batch Processing

**Test Command**:
```bash
# Create test directory
mkdir -p test-manifests
cp test-app.yaml test-manifests/
cp invalid-app.yaml test-manifests/
cat > test-manifests/another-app.yaml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: another-app
spec:
  project: default
  source:
    repoURL: https://github.com/test/repo2.git
    targetRevision: HEAD
    path: ./
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
EOF

# Run batch parser
argocd-parse --directory test-manifests --output-dir ./output

# Check summary
ls ./output/
```

**Expected Behavior**:
- Progress bar shown during processing
- 2 JSON files created (test-app.json, another-app.json)
- 1 file failed (invalid-app.yaml)
- Summary: "Total: 3, Successful: 2, Failed: 1"
- Exit code 0 (partial success allowed in batch mode)

---

## Notes

### Test Data Requirements

Create these test fixtures before integration testing:

**Valid Manifests** (`tests/contract/parser/fixtures/valid-manifests/`):
- `minimal-app.yaml`: Bare minimum required fields
- `full-app.yaml`: All optional fields present
- `helm-app.yaml`: Helm chart source (chart instead of path)
- `sync-policy-app.yaml`: Has automated syncPolicy

**Invalid Manifests** (`tests/contract/parser/fixtures/invalid-manifests/`):
- `missing-source.yaml`: No spec.source
- `empty-name.yaml`: metadata.name = ""
- `wrong-apiversion.yaml`: apiVersion = "v1"
- `wrong-kind.yaml`: kind = "Deployment"
- `multi-doc.yaml`: Multiple Application documents

### Configuration File Format

Create sample config for testing (`tests/contract/parser/fixtures/config.json`):
```json
{
  "clusterMappings": {
    "https://kubernetes.default.svc": "local-cluster",
    "https://prod.k8s.example.com": "prod-cluster"
  },
  "defaultLabels": {
    "environment": "test",
    "team": "platform"
  }
}
```

### Performance Testing

For task T105, use this script:
```bash
#!/bin/bash
# Generate 100 test manifests
for i in {1..100}; do
  cat > "test-manifests/app-$i.yaml" <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-$i
spec:
  project: default
  source:
    repoURL: https://github.com/test/repo.git
    targetRevision: main
    path: ./app-$i
  destination:
    server: https://kubernetes.default.svc
    namespace: ns-$i
EOF
done

# Time batch processing
time argocd-parse --directory test-manifests --output-dir ./output
```

Target: <30 seconds total, <5s per file for 1MB files

---

## Format Validation

All tasks follow the required checklist format:
- ✅ Checkbox prefix: `- [ ]`
- ✅ Task ID: T001-T105 (sequential)
- ✅ [P] marker: 28 parallelizable tasks marked
- ✅ [Story] label: All user story tasks tagged (US1, US2, US3)
- ✅ File paths: Included in all implementation tasks
- ✅ Clear descriptions: Action-oriented with specific deliverables

Total implementation tasks: 105
Tasks per story: US1=29, US2=21, US3=23
Setup/Foundation: 18 tasks
Polish: 14 tasks
