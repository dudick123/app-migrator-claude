---
description: "Task list for YAML File Scanner implementation"
---

# Tasks: YAML File Scanner

**Input**: Design documents from `/specs/001-yaml-scanner/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included in this implementation per constitution requirement (Principle II: Test Coverage Required).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below use single project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create Python project structure with src/scanner/ and tests/ directories
- [ ] T002 Initialize pyproject.toml with UV for Python 3.12+ project with dependencies: typer, rich, pydantic, pytest
- [ ] T003 [P] Create .python-version file specifying Python 3.12
- [ ] T004 [P] Create src/__init__.py and src/scanner/__init__.py package files
- [ ] T005 [P] Configure Ruff linting in pyproject.toml with strict settings
- [ ] T006 [P] Configure mypy or pyright in pyproject.toml for strict type checking

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create ScanOptions Pydantic model in src/scanner/core.py with fields: input_dir, recursive, format, verbosity
- [ ] T008 Add field validators to ScanOptions for input_dir existence and directory validation
- [ ] T009 Create ScanResult Pydantic model in src/scanner/core.py with fields: files, errors, computed properties: count, has_errors
- [ ] T010 Add to_json_array() method to ScanResult for JSON output format
- [ ] T011 [P] Create OutputFormat and VerbosityLevel type aliases in src/scanner/core.py
- [ ] T012 Create unit test file tests/unit/test_scanner_core.py with pytest fixtures for temp directories

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Scan Single Directory (Priority: P1) 🎯 MVP

**Goal**: Scan a single directory for YAML files with configurable output formats and verbosity levels

**Independent Test**: Point scanner at directory with known YAML files, verify all discovered with correct output format

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Write unit test for single directory scan in tests/unit/test_scanner_core.py::test_scan_single_directory
- [ ] T014 [P] [US1] Write unit test for .yaml and .yml extension discovery in tests/unit/test_scanner_core.py::test_both_extensions_discovered
- [ ] T015 [P] [US1] Write unit test for empty directory scan in tests/unit/test_scanner_core.py::test_empty_directory_returns_empty_list
- [ ] T016 [P] [US1] Write integration test for single directory scan in tests/integration/test_single_directory_scan.py

### Implementation for User Story 1

- [ ] T017 [P] [US1] Create is_yaml_file() function in src/scanner/filters.py to check file extensions (.yaml, .yml)
- [ ] T018 [P] [US1] Create scan_directory() function in src/scanner/core.py for non-recursive scanning using pathlib.glob()
- [ ] T019 [US1] Implement path resolution to absolute paths in scan_directory() function
- [ ] T020 [US1] Implement file deduplication logic in scan_directory() for symlink handling in non-recursive mode
- [ ] T021 [P] [US1] Create format_json_output() function in src/scanner/core.py to output JSON array to stdout
- [ ] T022 [P] [US1] Create format_human_output() function in src/scanner/core.py using Rich library for terminal formatting
- [ ] T023 [US1] Implement quiet verbosity (no output) in format_human_output()
- [ ] T024 [US1] Implement info verbosity (summary with count) in format_human_output()
- [ ] T025 [US1] Implement verbose verbosity (Rich table with all files) in format_human_output()
- [ ] T026 [US1] Create Typer CLI application in src/scanner/cli.py with main command
- [ ] T027 [US1] Add --input-dir/-i parameter to CLI with Path type and required=True
- [ ] T028 [US1] Add --format/-f parameter to CLI with choices: json, human (default: human)
- [ ] T029 [US1] Add --verbosity/-v parameter to CLI with choices: quiet, info, verbose (default: info)
- [ ] T030 [US1] Implement CLI parameter validation and error messages to stderr
- [ ] T031 [US1] Wire CLI parameters to ScanOptions model instantiation with error handling
- [ ] T032 [US1] Wire scan_directory() and output formatting functions to CLI command
- [ ] T033 [US1] Implement exit code logic: 0 for success, 1 for errors
- [ ] T034 [US1] Add entry point script 'argocd-scan' in pyproject.toml [project.scripts]

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Recursive Directory Scan (Priority: P2)

**Goal**: Enable recursive scanning of directory trees with hidden directory filtering and symlink cycle prevention

**Independent Test**: Create nested directory structure with YAML files at multiple levels and hidden directories, verify correct discovery

### Tests for User Story 2

- [ ] T035 [P] [US2] Write unit test for recursive scan discovering files at multiple depths in tests/unit/test_scanner_core.py::test_recursive_scan_multiple_depths
- [ ] T036 [P] [US2] Write unit test for non-recursive default behavior in tests/unit/test_scanner_core.py::test_non_recursive_default_only_top_level
- [ ] T037 [P] [US2] Write unit test for hidden directory filtering in tests/unit/test_filters.py::test_hidden_directories_skipped
- [ ] T038 [P] [US2] Write unit test for symlink ignoring in recursive mode in tests/unit/test_scanner_core.py::test_recursive_ignores_symlinks
- [ ] T039 [P] [US2] Write integration test for recursive scan in tests/integration/test_recursive_scan.py
- [ ] T040 [P] [US2] Write integration test for permission errors with partial results in tests/integration/test_permission_errors.py

### Implementation for User Story 2

- [ ] T041 [P] [US2] Create is_hidden_directory() function in src/scanner/filters.py to check for dot-prefixed directory names
- [ ] T042 [US2] Update scan_directory() function to support recursive parameter using pathlib.rglob()
- [ ] T043 [US2] Implement hidden directory filtering in recursive scan logic
- [ ] T044 [US2] Implement symlink ignoring in recursive mode (rglob doesn't follow symlinks by default in Python 3.10+)
- [ ] T045 [US2] Implement permission error handling with try/except in scan_directory()
- [ ] T046 [US2] Collect permission errors into ScanResult.errors list
- [ ] T047 [US2] Implement partial results with errors: output files to stdout, errors to stderr, exit code 1
- [ ] T048 [US2] Add --recursive/-r flag to CLI command in src/scanner/cli.py
- [ ] T049 [US2] Wire recursive parameter from CLI to ScanOptions model
- [ ] T050 [US2] Update exit code logic to return 1 when ScanResult.has_errors is True

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Add type annotations to all functions with return types
- [ ] T052 [P] Add docstrings to all public functions and classes
- [ ] T053 [P] Run mypy/pyright type checking and fix any type errors
- [ ] T054 [P] Run Ruff linting and fix any style issues
- [ ] T055 [P] Add CLI help text with detailed parameter descriptions in src/scanner/cli.py
- [ ] T056 Add README.md usage examples referencing io-artifact-examples/argocd-applications
- [ ] T057 [P] Verify all error messages go to stderr (not stdout)
- [ ] T058 [P] Verify JSON output is valid JSON array format
- [ ] T059 Run pytest with coverage report to ensure >80% coverage
- [ ] T060 Test CLI manually with io-artifact-examples/argocd-applications directory

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 and 2 can proceed in parallel after Foundational (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, but US2 extends scan_directory() from US1

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core models before scanning logic
- Scanning logic before CLI integration
- CLI integration before output formatting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a user story marked [P] can run in parallel
- Implementation tasks within a story marked [P] can run in parallel
- User Story 1 and 2 can be worked on in parallel by different team members after Foundational phase completes

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task T013: "Write unit test for single directory scan"
Task T014: "Write unit test for .yaml and .yml extension discovery"
Task T015: "Write unit test for empty directory scan"
Task T016: "Write integration test for single directory scan"

# Launch filter functions together:
Task T017: "Create is_yaml_file() function in src/scanner/filters.py"
Task T021: "Create format_json_output() function in src/scanner/core.py"
Task T022: "Create format_human_output() function in src/scanner/core.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with io-artifact-examples/
5. Ready for demo/deployment as basic scanner

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Each story adds value without breaking previous functionality

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (tests + implementation)
   - Developer B: User Story 2 (tests + implementation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach per constitution)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tasks include explicit file paths for clarity
- Exit codes and stdout/stderr separation are critical for pipeline integration
