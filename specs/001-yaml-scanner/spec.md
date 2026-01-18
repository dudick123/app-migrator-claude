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

1. **Given** a directory containing 5 YAML files, **When** I run the scanner on that directory with the input directory parameter, **Then** I receive a list of all 5 file paths.
2. **Given** a directory containing files with `.yaml` and `.yml` extensions, **When** I run the scanner, **Then** both extension types are discovered.
3. **Given** a directory containing no YAML files, **When** I run the scanner, **Then** I receive an empty list with no errors.
4. **Given** I want to understand how to use the scanner, **When** I invoke the help parameter, **Then** I see usage information including all available parameters and their descriptions.
5. **Given** a directory with 10 YAML files, **When** I run the scanner with informational output verbosity, **Then** I see a summary showing "10 files found" without individual file details.
6. **Given** a directory with 3 YAML files, **When** I run the scanner with verbose output verbosity, **Then** I see detailed messages for each file discovered and each directory scanned.
7. **Given** a directory with YAML files, **When** I run the scanner with no output verbosity, **Then** I see no messages unless an error occurs.

---

### User Story 2 - Recursive Directory Scan (Priority: P2)

As a DevOps engineer, I want to recursively scan a directory tree for YAML files so that I can discover all ArgoCD manifests across a complex repository structure.

**Why this priority**: Many organizations store ArgoCD manifests in nested directory structures (e.g., by environment, cluster, or application). Recursive scanning is essential for comprehensive discovery.

**Independent Test**: Can be fully tested by creating a nested directory structure with YAML files at various depths and verifying all are discovered.

**Acceptance Scenarios**:

1. **Given** a directory tree with YAML files at depth levels 1, 2, and 3, **When** I run the scanner with the recursive parameter enabled, **Then** all files at all depths are discovered.
2. **Given** the recursive parameter is not specified (default off), **When** I run the scanner on a directory with subdirectories, **Then** only top-level YAML files are returned.
3. **Given** a deeply nested structure (10+ levels), **When** I run the scanner with the recursive parameter enabled, **Then** all YAML files are discovered regardless of depth.
4. **Given** a directory tree containing hidden directories (`.git`, `.cache`) with YAML files inside them, **When** I run the scanner with the recursive parameter enabled, **Then** those hidden directories are skipped and their YAML files are not discovered.

---

### Edge Cases

- What happens when no input directory parameter is provided? Scanner reports an error indicating the input directory is required.
- What happens when an invalid output verbosity level is specified? Scanner reports an error listing the valid verbosity options.
- What happens when a directory path does not exist? Scanner reports a clear error message indicating the path was not found.
- What happens when a directory is not readable due to permissions? Scanner reports a permission error for that directory and continues scanning accessible paths.
- What happens when symbolic links point to YAML files? Scanner follows symlinks by default and includes the linked files.
- What happens when a file has a YAML extension but is not valid YAML? Scanner includes the file (validation is the Parser stage's responsibility).
- What happens when the same file is reachable via multiple symlink paths? Scanner reports each unique file only once (deduplicated by resolved path).
- What happens when hidden directories (starting with `.`) are encountered? Scanner skips hidden directories entirely and does not traverse into them.

## Requirements *(mandatory)*

### Functional Requirements

#### CLI Parameters

- **FR-001**: Scanner MUST provide a help parameter that displays usage information and all available parameters.
- **FR-002**: Scanner MUST accept an input directory parameter to specify the directory to scan.
- **FR-003**: Scanner MUST accept an output verbosity parameter with three levels:
  - **No output**: Suppress all non-error messages (only errors displayed)
  - **Informational**: Display summary messages (files found count, scan completion)
  - **Verbose**: Display detailed processing messages (each file discovered, each directory scanned, YAML validation status)
- **FR-004**: Scanner MUST accept a recursive parameter to enable/disable subdirectory traversal (disabled by default).

#### Scanning Behavior

- **FR-005**: Scanner MUST discover all files with `.yaml` extension in the specified directory.
- **FR-006**: Scanner MUST discover all files with `.yml` extension in the specified directory.
- **FR-007**: Scanner MUST return the absolute path for each discovered file.
- **FR-008**: Scanner MUST report an error when the specified path does not exist.
- **FR-009**: Scanner MUST report an error when the specified path is not a directory.
- **FR-010**: Scanner MUST handle permission errors gracefully, reporting inaccessible paths without crashing.
- **FR-011**: Scanner MUST follow symbolic links when discovering files.
- **FR-012**: Scanner MUST deduplicate files reachable via multiple paths (using resolved absolute path).
- **FR-013**: Scanner MUST skip hidden directories (directories whose names start with `.`) during traversal.

### Key Entities

- **ScanResult**: Represents the output of a scan operation. Contains: list of discovered file paths, count of files found, count of directories scanned, list of any errors encountered (path + error message).
- **ScanOptions**: Configuration for a scan operation. Contains: input directory path (required), recursive flag (boolean, default: false), output verbosity level (no output / informational / verbose, default: informational).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scanner discovers 100% of YAML/YML files in a test directory structure with known file counts.
- **SC-002**: Scanner completes scanning of 10,000 files in under 5 seconds on standard hardware.
- **SC-003**: Scanner correctly handles and reports 100% of permission errors without crashing.
- **SC-004**: Users can understand scanner output and identify discovered files within 10 seconds of viewing results.
- **SC-005**: Users can successfully invoke the help parameter and understand all available options within 30 seconds.

## Assumptions

- Users have read access to the majority of directories they intend to scan.
- The file system being scanned is a local or network-mounted file system (not cloud object storage).
- YAML files use standard `.yaml` or `.yml` extensions (non-standard extensions like `.yamlx` are out of scope).
- Symbolic link cycles, if present, are handled by the underlying file system or standard library traversal.
- Hidden directories (starting with `.`) typically contain tool/system files not relevant to ArgoCD manifests (e.g., `.git`, `.venv`, `.cache`).
