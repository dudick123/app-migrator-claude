# ArgoCD Application Migrator

A CLI tool for migrating ArgoCD Applications to JSON configuration format using a 4-stage pipeline architecture.

## Overview

The ArgoCD Application Migrator is a Python-based command-line tool designed to help DevOps engineers migrate ArgoCD Application manifests from YAML to JSON configuration format. The tool uses a 4-stage pipeline:

1. **Scanner** (✅ Current) - Discover `*.yaml`/`*.yml` files in directories
2. **Parser** (🚧 Planned) - Extract fields from valid ArgoCD Applications
3. **Migrator** (🚧 Planned) - Transform to JSON config (1:1 mapping)
4. **Validator** (🚧 Planned) - Validate against JSON Schema

### Current Status

**Phase 1: YAML File Scanner** - The scanner stage is currently implemented and ready for use.

---

## Features

### YAML File Scanner (Stage 1)

- ✅ Discover `.yaml` and `.yml` files in specified directories
- ✅ Recursive directory traversal with hidden directory filtering
- ✅ Multiple output formats (JSON array, human-readable)
- ✅ Configurable verbosity levels (quiet, info, verbose)
- ✅ Graceful error handling with partial results
- ✅ Unix-compliant stdout/stderr/exit code conventions
- ✅ Cross-platform support (macOS, Linux, Windows)

---

## Installation

### Prerequisites

- **Python 3.12+** (required)
- **UV package manager** (recommended)

### Step 1: Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/argocd-migrator.git
cd argocd-migrator

# Sync dependencies with UV
uv sync

# Verify installation
uv run argocd-scan --help
```

---

## Quick Start

### Basic Usage

Scan a directory for YAML files:

```bash
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications
```

**Output**:
```
Found 2 YAML files
```

### JSON Output

Get a JSON array of discovered file paths:

```bash
uv run argocd-scan --input-dir ./argocd-applications --format json
```

**Output**:
```json
[
  "/absolute/path/to/app1.yaml",
  "/absolute/path/to/app2.yml"
]
```

### Recursive Scanning

Scan directory tree recursively:

```bash
uv run argocd-scan --input-dir ./argocd --recursive --format json
```

---

## Usage

### Command Syntax

```bash
argocd-scan [OPTIONS]
```

### Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--input-dir` | `-i` | path | *required* | Directory to scan for YAML files |
| `--recursive` | `-r` | flag | `false` | Enable recursive subdirectory scanning |
| `--format` | `-f` | `json`\|`human` | `human` | Output format |
| `--verbosity` | `-v` | `quiet`\|`info`\|`verbose` | `info` | Output verbosity level |
| `--help` | `-h` | flag | - | Show help message and exit |

### Output Formats

**JSON Format** (`--format json`):
- Simple JSON array of absolute file paths
- Suitable for piping to other tools
- Always writes to stdout

**Human Format** (`--format human`):
- Formatted terminal output with colors and tables (using Rich library)
- Three verbosity levels:
  - `quiet`: No output (errors only)
  - `info`: Summary (file count)
  - `verbose`: Detailed table of all files

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success - scan completed without errors |
| `1` | Error - invalid parameters, missing directory, or permission errors |

---

## Examples

### Example 1: Scan ArgoCD Applications Directory

```bash
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications
```

**Expected Output**:
```
Found 2 YAML files
```

---

### Example 2: Recursive JSON Scan

```bash
uv run argocd-scan --input-dir ./argocd --recursive --format json
```

**Expected Output**:
```json
["/Users/you/argocd/prod/app1.yaml", "/Users/you/argocd/staging/app2.yml"]
```

---

### Example 3: Verbose Output with Rich Formatting

```bash
uv run argocd-scan --input-dir ./apps --verbosity verbose
```

**Expected Output**:
```
╭──────────────── Found 2 YAML files ────────────────╮
│ /Users/you/apps/app1.yaml                          │
│ /Users/you/apps/app2.yml                           │
╰────────────────────────────────────────────────────╯
```

---

### Example 4: Pipeline Integration

```bash
# Count YAML files using jq
uv run argocd-scan --input-dir ./apps --format json | jq 'length'

# Save discovered files
uv run argocd-scan --input-dir ./apps --format json > files.json

# Filter results
uv run argocd-scan --input-dir ./apps --format json | jq '.[] | select(contains("prod"))'
```

---

### Example 5: Error Handling

```bash
# Scan with permission errors - get partial results
uv run argocd-scan --input-dir /var/argocd --recursive --format json 2> errors.log

# Check errors
cat errors.log
```

**Output (stdout)**: JSON array of accessible files
**Output (stderr)**: Permission error messages
**Exit Code**: 1

---

## Architecture

### Pipeline Pattern

The ArgoCD Migrator follows a 4-stage pipeline architecture:

```
Scanner → Parser → Migrator → Validator
```

Each stage:
- Is independently testable
- Has clear input/output contracts
- Reports progress and errors
- Continues processing on individual file failures

### Current Implementation

**Stage 1: Scanner** ✅ Implemented
- Input: Directory path + options
- Output: JSON array of YAML file paths
- Features: Recursive scan, hidden directory filtering, symlink handling

**Stage 2: Parser** 🚧 Planned
- Input: List of YAML file paths
- Output: Extracted ArgoCD Application fields
- Features: YAML parsing, field extraction, validation

**Stage 3: Migrator** 🚧 Planned
- Input: Extracted application data
- Output: JSON configuration
- Features: 1:1 mapping, transformation rules

**Stage 4: Validator** 🚧 Planned
- Input: JSON configuration
- Output: Validation results
- Features: JSON Schema (Draft7Validator) validation

---

## Project Structure

```
argocd-migrator/
├── src/
│   └── scanner/              # Scanner stage implementation
│       ├── __init__.py
│       ├── core.py           # Core scanning logic
│       ├── filters.py        # Filtering logic (hidden dirs, extensions)
│       └── cli.py            # Typer CLI application
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data
├── specs/
│   └── 001-yaml-scanner/     # Scanner specification & design docs
│       ├── spec.md           # Feature specification
│       ├── plan.md           # Implementation plan
│       ├── data-model.md     # Data structures
│       ├── quickstart.md     # User guide
│       └── contracts/        # CLI interface contracts
├── io-artifact-examples/
│   └── argocd-applications/  # Example ArgoCD Application YAML files
├── pyproject.toml            # UV project configuration
├── README.md                 # This file
└── .python-version           # Python 3.12+
```

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/argocd-migrator.git
cd argocd-migrator

# Install development dependencies
uv sync --all-extras

# Install pre-commit hooks (if using)
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_scanner_core.py

# Run specific test
uv run pytest tests/unit/test_scanner_core.py::test_scan_single_directory
```

### Type Checking

```bash
# Run mypy or pyright
uv run mypy src/
uv run pyright src/
```

### Linting

```bash
# Run Ruff
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
```

---

## Configuration

### Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: UV
- **CLI Framework**: Typer
- **Terminal Output**: Rich
- **Data Validation**: Pydantic
- **YAML Parsing**: PyYAML (future stages)
- **Schema Validation**: jsonschema (future stages)
- **Testing**: pytest
- **Type Checking**: mypy or pyright
- **Linting**: Ruff

### Performance

- **Scan Performance**: 10,000 files in under 5 seconds
- **Memory Usage**: <512MB for standard operations
- **CLI Response**: Help/validation within 500ms

---

## Troubleshooting

### "Command not found: argocd-scan"

**Solution**: Use `uv run` to execute the command:

```bash
uv run argocd-scan --help
```

### "Directory does not exist"

**Solution**: Check the path and use absolute paths:

```bash
# Use absolute path
uv run argocd-scan --input-dir /absolute/path/to/directory

# Or verify current directory
pwd
uv run argocd-scan --input-dir ./relative/path
```

### "Permission denied" errors

**Expected Behavior**: Scanner continues with accessible files and returns exit code 1.

**Solution**: Capture errors separately:

```bash
uv run argocd-scan --input-dir /apps --format json 2> errors.log
```

### No files found

**Check**:
1. Files have `.yaml` or `.yml` extensions
2. Files are not in hidden directories (starting with `.`)
3. Path is correct

```bash
# Verify files exist
ls ./directory/*.yaml ./directory/*.yml
```

---

## Documentation

Detailed documentation is available in the `specs/001-yaml-scanner/` directory:

- **[Specification](specs/001-yaml-scanner/spec.md)** - Feature requirements and acceptance criteria
- **[Implementation Plan](specs/001-yaml-scanner/plan.md)** - Technical design and architecture
- **[Data Model](specs/001-yaml-scanner/data-model.md)** - Data structures and validation
- **[CLI Contract](specs/001-yaml-scanner/contracts/cli-interface.md)** - Interface specification
- **[Quickstart Guide](specs/001-yaml-scanner/quickstart.md)** - Detailed usage examples

---

## Contributing

### Code Standards

- Python 3.12+ with type annotations
- Strict type checking (mypy/pyright in strict mode)
- Ruff for linting (strict configuration)
- Test coverage required for all code
- Follow PEP 8 style guidelines

### Testing Requirements

- All public functions must have unit tests
- Integration tests for user scenarios
- Type safety verified with mypy/pyright
- All tests must pass before merge

---

## License

[Your License Here]

---

## Support

For issues or questions:
1. Check the [Quickstart Guide](specs/001-yaml-scanner/quickstart.md)
2. Review [CLI Contract](specs/001-yaml-scanner/contracts/cli-interface.md)
3. Consult specification documents in `specs/001-yaml-scanner/`
4. Open an issue on GitHub

---

## Roadmap

- [x] **Phase 1**: YAML File Scanner (Current)
- [ ] **Phase 2**: ArgoCD Application Parser
- [ ] **Phase 3**: JSON Configuration Migrator
- [ ] **Phase 4**: JSON Schema Validator
- [ ] **Phase 5**: Full Pipeline Integration
- [ ] **Phase 6**: CI/CD Integration Examples

---

## Example ArgoCD Applications

Sample ArgoCD Application manifests are provided in `io-artifact-examples/argocd-applications/`:

- `app-1.yaml` - Basic Application with sync policy
- `app-2.yaml` - Application with directory source

Use these for testing:

```bash
uv run argocd-scan --input-dir ./io-artifact-examples/argocd-applications --format json
```

**Expected Output**:
```json
[
  "/path/to/argocd-migrator/io-artifact-examples/argocd-applications/app-1.yaml",
  "/path/to/argocd-migrator/io-artifact-examples/argocd-applications/app-2.yaml"
]
```
