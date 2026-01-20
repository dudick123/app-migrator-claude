# Feature Specification: ArgoCD YAML Parser

**Feature Branch**: `002-argocd-yaml-parser`
**Created**: 2026-01-18
**Status**: Draft
**Input**: User description: "let's make the cli capable of parsing yaml files that are valid argocd application manifest files. when an argocd yaml application manifest file is parsed, and considers valid, relevant fields in the manifest will be used for output and mapping to a json configuration file"

## Clarifications

### Session 2026-01-18

- Q: When the CLI processes a single ArgoCD manifest file and produces JSON output, where should the JSON file be written? → A: A dedicated output directory specified by the user via CLI flag (required)
- Q: How should the CLI handle a YAML file containing multiple ArgoCD Application documents? → A: Reject the file with an error message stating multi-document YAML is not supported
- Q: How should the CLI handle ArgoCD manifests with custom/extended fields not in the standard schema? → A: Ignore non-standard fields silently and only extract known standard fields
- Q: What should happen when required fields are present but contain empty/null values? → A: Reject the manifest as invalid (treat empty/null as missing required fields)
- Q: What should the CLI do when the user-specified output directory does not exist? → A: Automatically create the output directory (and parent directories if needed)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parse Valid ArgoCD Application Manifest (Priority: P1)

Users need to process existing ArgoCD application manifest YAML files to extract configuration information into a standardized JSON format. This enables migration planning, configuration analysis, and integration with other tools.

**Why this priority**: This is the core functionality - without the ability to parse and validate ArgoCD manifests, no other features can work. This delivers immediate value by enabling users to extract structured data from their existing ArgoCD configurations.

**Independent Test**: Can be fully tested by providing a valid ArgoCD application manifest YAML file to the CLI and verifying that it produces a correctly structured JSON output with all relevant fields mapped.

**Acceptance Scenarios**:

1. **Given** a valid ArgoCD application manifest YAML file, **When** the user runs the CLI with the file path and output directory flag, **Then** the system validates the manifest structure and outputs a JSON file to the specified directory with mapped configuration fields
2. **Given** a valid ArgoCD manifest with all standard fields (name, namespace, source, destination), **When** the CLI parses the file, **Then** all fields are correctly extracted and mapped to the JSON output schema
3. **Given** a valid ArgoCD manifest with optional fields (syncPolicy, ignoreDifferences, etc.), **When** the CLI parses the file, **Then** optional fields are included in the JSON output when present
4. **Given** a valid ArgoCD manifest with custom/non-standard fields, **When** the CLI parses the file, **Then** only the known standard and optional fields are extracted and custom fields are silently ignored
5. **Given** a valid ArgoCD manifest and a non-existent output directory path, **When** the CLI runs, **Then** the output directory (and any necessary parent directories) are created automatically and the JSON file is written successfully

---

### User Story 2 - Detect and Report Invalid Manifests (Priority: P2)

Users need clear feedback when a YAML file is not a valid ArgoCD application manifest, helping them identify configuration issues or incorrect file selection. When invalid files are provided, the CLI should report specific validation errors.

**Why this priority**: Validation and error reporting are essential for usability but secondary to basic parsing. Users need to know when files are invalid, but this can be implemented after core parsing works.

**Independent Test**: Can be fully tested by providing various invalid YAML files (malformed YAML, non-ArgoCD manifests, missing required fields) and verifying that the CLI rejects them with clear, actionable error messages.

**Acceptance Scenarios**:

1. **Given** a YAML file that is not an ArgoCD application manifest, **When** the user runs the CLI, **Then** the system reports that the file is invalid with a clear error message
2. **Given** a YAML file with malformed syntax, **When** the CLI attempts to parse it, **Then** the system reports a YAML parsing error with line/column information
3. **Given** an ArgoCD manifest missing required fields (e.g., no spec.source), **When** the CLI validates it, **Then** the system reports which required fields are missing
4. **Given** a YAML file containing multiple ArgoCD Application documents, **When** the CLI validates it, **Then** the system rejects the file with an error message stating multi-document YAML is not supported
5. **Given** an ArgoCD manifest with required fields that have empty string or null values (e.g., metadata.name: ""), **When** the CLI validates it, **Then** the system rejects the manifest and reports the fields with empty/null values as invalid

---

### User Story 3 - Batch Process Multiple Manifests (Priority: P3)

Users need to process multiple ArgoCD manifest files at once to analyze entire application portfolios or migration batches efficiently.

**Why this priority**: Batch processing adds convenience and efficiency but isn't required for initial value delivery. Single-file processing must work first.

**Independent Test**: Can be fully tested by providing a directory containing multiple valid and invalid ArgoCD manifests and verifying that the CLI processes all files, generates individual JSON outputs, and produces a summary report.

**Acceptance Scenarios**:

1. **Given** a directory containing multiple ArgoCD manifest YAML files, **When** the user runs the CLI with the directory path and output directory flag, **Then** the system processes all manifest files and outputs individual JSON files to the specified output directory for each valid manifest
2. **Given** a batch processing operation with both valid and invalid files, **When** the CLI completes, **Then** the system provides a summary showing successful parses, validation failures, and error details
3. **Given** multiple manifests in a directory, **When** batch processing runs, **Then** one invalid file does not prevent processing of other valid files

---

### Edge Cases

- YAML files containing multiple ArgoCD application documents will be rejected with a clear error message (multi-document YAML is not supported)
- ArgoCD manifests with custom/extended fields not in the standard v1alpha1 schema will have those non-standard fields ignored silently; only known standard fields will be extracted
- What happens when the YAML file is valid but extremely large (e.g., 10MB+)?
- How does the system handle special characters or non-ASCII content in manifest fields (app names, labels, annotations)?
- Required fields that are present in the YAML structure but contain empty strings or null values will be treated as missing and result in manifest rejection with a validation error
- How does the system handle different ArgoCD API versions (v1alpha1 vs future versions)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept file paths to ArgoCD application manifest YAML files as input and require users to specify an output directory via CLI flag where JSON files will be written (output directory will be created automatically if it does not exist)
- **FR-002**: System MUST validate that input YAML files conform to the ArgoCD Application CRD schema (kind: Application, apiVersion: argoproj.io/v1alpha1) and contain exactly one document (reject multi-document YAML files with an error message)
- **FR-003**: System MUST extract only the following standard fields from valid manifests: metadata.name, metadata.namespace, spec.project, spec.source (repo, path, targetRevision), spec.destination (server, namespace)
- **FR-004**: System MUST extract only the following optional fields when present: spec.syncPolicy, spec.ignoreDifferences, spec.info, metadata.labels, metadata.annotations (non-standard/custom fields are silently ignored)
- **FR-005**: System MUST output extracted configuration data in JSON format with a well-defined schema
- **FR-006**: System MUST report validation errors with specific details about what failed (e.g., missing required fields, incorrect structure, invalid field values, empty/null required fields)
- **FR-006a**: System MUST treat required fields with empty string ("") or null values as missing/invalid and reject the manifest with an appropriate error message
- **FR-007**: System MUST handle both single file and directory/batch processing modes
- **FR-008**: System MUST preserve data types from the YAML manifest in the JSON output (strings, numbers, booleans, arrays, objects)
- **FR-009**: System MUST generate output JSON files with meaningful names derived from the source manifest (e.g., based on application name)
- **FR-010**: System MUST provide user feedback during processing (progress indication for batch operations, success/failure messages)
- **FR-011**: System MUST automatically create the output directory (including parent directories) if it does not exist before writing JSON files

### Key Entities

- **ArgoCD Application Manifest**: A YAML file containing Kubernetes CustomResource definition for ArgoCD Application (kind: Application, apiVersion: argoproj.io/v1alpha1) with metadata, spec, and optional status sections
- **JSON Configuration Output**: A structured JSON document containing extracted and normalized fields from the ArgoCD manifest, following a defined schema for downstream consumption
- **Validation Result**: Contains success/failure status, error messages, and details about which validation rules passed or failed
- **Field Mapping**: Defines the relationship between ArgoCD manifest YAML paths (e.g., spec.source.repoURL) and corresponding JSON output structure

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can process a valid ArgoCD application manifest file and receive JSON output in under 5 seconds for files up to 1MB
- **SC-002**: System correctly validates and accepts 100% of valid ArgoCD v1alpha1 application manifests from the official ArgoCD examples repository
- **SC-003**: System correctly rejects invalid manifests with actionable error messages that specify the validation failure
- **SC-004**: Users can process directories containing up to 100 manifest files with complete success/failure reporting
- **SC-005**: The JSON output schema includes all standard ArgoCD application fields required for migration planning (source repository, deployment target, sync configuration)
- **SC-006**: 95% of users can successfully parse their first ArgoCD manifest file without consulting documentation

## Assumptions

- ArgoCD manifests follow the v1alpha1 API version (argoproj.io/v1alpha1) as this is the current stable version
- Users have valid YAML files accessible on their local filesystem
- Output JSON schema can be defined based on common migration tool requirements (repository information, deployment targets, sync policies)
- YAML files are text files with UTF-8 encoding
- Users running the CLI have read permissions on input files and write permissions on the parent directory where the output directory will be created (or the output directory itself if it already exists)
- Each YAML file contains exactly one ArgoCD Application document (multi-document YAML files are not supported and will be rejected)
- The JSON output does not need to be reversible back to YAML (one-way transformation is acceptable)

## Scope

### In Scope

- Parsing and validating ArgoCD Application manifest YAML files (v1alpha1)
- Extracting standard and optional fields from the manifest spec
- Mapping extracted data to a defined JSON schema
- Single file and batch/directory processing
- Validation error reporting with specific failure details
- JSON output file generation

### Out of Scope

- Parsing other ArgoCD resource types (AppProject, ApplicationSet, etc.)
- Connecting to live ArgoCD servers or Kubernetes clusters
- Modifying or generating ArgoCD manifests
- Converting JSON back to YAML format
- Processing ArgoCD Application status fields (read-only runtime state)
- Handling future ArgoCD API versions beyond v1alpha1 (will be addressed when they become stable)
- GUI or web interface for parsing (CLI only)
