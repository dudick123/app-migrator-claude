# Feature Specification: YAML File Scanner

**Feature Branch**: `001-yaml-scanner`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "YAML file scanner stage - discover and enumerate YAML/YML files for ArgoCD Application migration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scan Single Directory (Priority: P1)

As a DevOps engineer, I want to scan a single directory for YAML files so that I can quickly discover ArgoCD Application manifests in a known location.

**Why this priority**: This is the most common use case - users typically know where their ArgoCD manifests are stored and want to scan that specific directory.

**Independent Test**: Can be fully tested by pointing the scanner at a directory containing YAML files and verifying all files are discovered.

**Acceptance Scenarios**:

1. **Given** a directory containing 5 YAML files, **When** I run the scanner on that directory, **Then** I receive a list of all 5 file paths.
2. **Given** a directory containing files with `.yaml` and `.yml` extensions, **When** I run the scanner, **Then** both extension types are discovered.
3. **Given** a directory containing no YAML files, **When** I run the scanner, **Then** I receive an empty list with no errors.

---

### User Story 2 - Recursive Directory Scan (Priority: P2)

As a DevOps engineer, I want to recursively scan a directory tree for YAML files so that I can discover all ArgoCD manifests across a complex repository structure.

**Why this priority**: Many organizations store ArgoCD manifests in nested directory structures (e.g., by environment, cluster, or application). Recursive scanning is essential for comprehensive discovery.

**Independent Test**: Can be fully tested by creating a nested directory structure with YAML files at various depths and verifying all are discovered.

**Acceptance Scenarios**:

1. **Given** a directory tree with YAML files at depth levels 1, 2, and 3, **When** I run the scanner with recursive mode enabled, **Then** all files at all depths are discovered.
2. **Given** recursive mode is disabled (default), **When** I run the scanner on a directory with subdirectories, **Then** only top-level YAML files are returned.
3. **Given** a deeply nested structure (10+ levels), **When** I run the scanner recursively, **Then** all YAML files are discovered regardless of depth.

---

### User Story 3 - Progress Reporting (Priority: P3)

As a DevOps engineer scanning a large repository, I want to see progress updates so that I know the scanner is working and can estimate completion time.

**Why this priority**: For repositories with thousands of files, users need feedback that the operation is progressing. This supports the constitution's requirement for progress reporting on operations >5 seconds.

**Independent Test**: Can be fully tested by scanning a directory with many files and verifying progress output is displayed.

**Acceptance Scenarios**:

1. **Given** a directory with 1000+ files, **When** I run the scanner, **Then** I see periodic progress updates showing files scanned.
2. **Given** the scanner is running, **When** progress updates occur, **Then** each update shows the current count of discovered YAML files.

---

### Edge Cases

- What happens when a directory path does not exist? Scanner reports a clear error message indicating the path was not found.
- What happens when a directory is not readable due to permissions? Scanner reports a permission error for that directory and continues scanning accessible paths.
- What happens when symbolic links point to YAML files? Scanner follows symlinks by default and includes the linked files.
- What happens when a file has a YAML extension but is not valid YAML? Scanner includes the file (validation is the Parser stage's responsibility).
- What happens when the same file is reachable via multiple symlink paths? Scanner reports each unique file only once (deduplicated by resolved path).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Scanner MUST discover all files with `.yaml` extension in the specified directory.
- **FR-002**: Scanner MUST discover all files with `.yml` extension in the specified directory.
- **FR-003**: Scanner MUST support a flag to enable recursive directory traversal (disabled by default).
- **FR-004**: Scanner MUST return the absolute path for each discovered file.
- **FR-005**: Scanner MUST report an error when the specified path does not exist.
- **FR-006**: Scanner MUST report an error when the specified path is not a directory.
- **FR-007**: Scanner MUST handle permission errors gracefully, reporting inaccessible paths without crashing.
- **FR-008**: Scanner MUST follow symbolic links when discovering files.
- **FR-009**: Scanner MUST deduplicate files reachable via multiple paths (using resolved absolute path).
- **FR-010**: Scanner MUST report progress for operations scanning more than 100 files.
- **FR-011**: Scanner MUST support output in both human-readable and JSON formats.

### Key Entities

- **ScanResult**: Represents the output of a scan operation. Contains: list of discovered file paths, count of files found, count of directories scanned, list of any errors encountered (path + error message).
- **ScanOptions**: Configuration for a scan operation. Contains: target directory path, recursive flag (boolean), follow symlinks flag (boolean).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scanner discovers 100% of YAML/YML files in a test directory structure with known file counts.
- **SC-002**: Scanner completes scanning of 10,000 files in under 5 seconds on standard hardware.
- **SC-003**: Scanner provides progress updates at least every 2 seconds during long-running operations.
- **SC-004**: Scanner correctly handles and reports 100% of permission errors without crashing.
- **SC-005**: Users can understand scanner output and identify discovered files within 10 seconds of viewing results.

## Assumptions

- Users have read access to the majority of directories they intend to scan.
- The file system being scanned is a local or network-mounted file system (not cloud object storage).
- YAML files use standard `.yaml` or `.yml` extensions (non-standard extensions like `.yamlx` are out of scope).
- Symbolic link cycles, if present, are handled by the underlying file system or standard library traversal.
