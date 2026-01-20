# Quickstart Guide: ArgoCD YAML Parser

**Feature**: 002-argocd-yaml-parser
**Date**: 2026-01-18
**Version**: 1.0.0

## Overview

The ArgoCD YAML Parser is a CLI tool (Pipeline Stage 2) that parses and validates ArgoCD Application manifests (v1alpha1), transforming them into a standardized JSON format for migration planning and analysis.

---

## Installation

### Prerequisites

- Python 3.12 or higher
- UV package manager (recommended) or pip

### Install from Source

```bash
# Clone the repository
git clone https://github.com/org/app-migrator-claude.git
cd app-migrator-claude

# Install with UV (recommended)
uv sync

# Or install with pip
pip install -e .
```

After installation, the `argocd-parse` command will be available in your PATH.

---

## Basic Usage

### Single File Parsing

Parse a single ArgoCD Application manifest:

```bash
argocd-parse --file path/to/application.yaml --output-dir ./output
```

**Input**: `application.yaml`
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

**Output**: `./output/example-app.json`
```json
{
  "metadata": {
    "name": "example-app",
    "annotations": {
      "syncWave": "40"
    },
    "labels": {}
  },
  "project": "default",
  "source": {
    "repoURL": "https://github.com/org/repo.git",
    "revision": "main",
    "manifestPath": "./manifests",
    "directory": {
      "recurse": true
    }
  },
  "destination": {
    "clusterName": "default",
    "namespace": "default"
  },
  "enableSyncPolicy": false
}
```

---

### Batch Processing (Directory)

Parse all ArgoCD manifests in a directory:

```bash
argocd-parse --directory ./argocd-apps --output-dir ./output
```

**Features**:
- Recursively finds all `*.yaml` and `*.yml` files
- Processes each file independently
- Skips invalid files with detailed error messages
- Generates summary report

**Example Output**:
```
⠹ Processing example-app.yaml ━━━━━━━━━━━━━━━╸━━━━━━━━━━ 60% • 0:00:05
✓ example-app.yaml: example-app
✗ invalid-app.yaml: Field 'metadata.name' cannot be empty
✓ guestbook.yaml: guestbook
⊘ not-argocd.yaml: Not an ArgoCD Application
✓ helm-app.yaml: my-helm-app

Batch Summary:
  Total: 5
  Successful: 3
  Failed: 1
  Skipped: 1
  Success Rate: 60.0%
```

---

## CLI Options

### Required Arguments

| Flag | Short | Description | Example |
|------|-------|-------------|---------|
| `--file` | `-f` | Single YAML file to parse | `--file app.yaml` |
| `--directory` | `-d` | Directory to scan for YAML files | `--directory ./apps` |
| `--output-dir` | `-o` | Output directory for JSON files (required) | `--output-dir ./output` |

**Note**: Either `--file` or `--directory` must be specified, but not both.

### Optional Arguments

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--json` | | Output results in JSON format (for automation) | `false` (human-readable) |
| `--config` | `-c` | Path to configuration file | `None` |
| `--quiet` | `-q` | Suppress progress output | `false` |
| `--verbose` | `-v` | Enable verbose logging | `false` |
| `--help` | `-h` | Show help message | - |

### Examples

```bash
# Single file with JSON output (for CI/CD)
argocd-parse --file app.yaml --output-dir ./output --json

# Batch processing with custom config
argocd-parse --directory ./apps --output-dir ./output --config config.json

# Quiet mode (no progress bar)
argocd-parse --directory ./apps --output-dir ./output --quiet

# Verbose logging
argocd-parse --file app.yaml --output-dir ./output --verbose
```

---

## Configuration File

Use a configuration file to customize parser behavior:

### config.json

```json
{
  "clusterMappings": {
    "https://kubernetes.default.svc": "prod-cluster",
    "https://k8s.staging.example.com": "staging-cluster"
  },
  "defaultLabels": {
    "environment": "dev",
    "team": "platform"
  },
  "outputFormat": {
    "indent": 2,
    "sortKeys": true
  }
}
```

### Configuration Options

#### clusterMappings

Maps Kubernetes API server URLs to cluster names for the JSON output.

```json
{
  "clusterMappings": {
    "https://kubernetes.default.svc": "prod-cluster",
    "https://10.0.0.1:6443": "qa-cluster"
  }
}
```

**Behavior**:
- If a `destination.server` URL matches a key, use the mapped cluster name
- If no match found, use `destination.name` if present
- Otherwise, use `"default"` as cluster name

#### defaultLabels

Labels to add to all parsed applications (if not already present in the manifest).

```json
{
  "defaultLabels": {
    "environment": "production",
    "team": "devops",
    "managed-by": "argocd-migrator"
  }
}
```

**Behavior**:
- Default labels are added to `metadata.labels` in output
- Labels from the manifest take precedence over defaults
- If `metadata.labels` is absent, defaults are used

#### outputFormat

Controls JSON output formatting.

```json
{
  "outputFormat": {
    "indent": 2,
    "sortKeys": true,
    "ensureAscii": false
  }
}
```

---

## Output Structure

### JSON Output Schema

The parser transforms ArgoCD manifests into a normalized JSON format:

```json
{
  "metadata": {
    "name": "string",
    "annotations": {
      "key": "value"
    },
    "labels": {
      "key": "value"
    }
  },
  "project": "string",
  "source": {
    "repoURL": "string",
    "revision": "string",
    "manifestPath": "string | null",
    "directory": {
      "recurse": "boolean"
    }
  },
  "destination": {
    "clusterName": "string",
    "namespace": "string"
  },
  "enableSyncPolicy": "boolean"
}
```

### Field Transformations

| ArgoCD YAML Path | JSON Output Path | Transformation |
|------------------|------------------|----------------|
| `metadata.name` | `metadata.name` | Direct copy |
| `metadata.annotations` | `metadata.annotations` | Keys normalized (camelCase, namespace removed) |
| `spec.project` | `project` | Flatten to root level |
| `spec.source.repoURL` | `source.repoURL` | Direct copy |
| `spec.source.targetRevision` | `source.revision` | Renamed field |
| `spec.source.path` | `source.manifestPath` | Renamed field |
| `spec.destination.server` | `destination.clusterName` | Mapped via config |
| `spec.destination.namespace` | `destination.namespace` | Direct copy |
| `spec.syncPolicy` (presence) | `enableSyncPolicy` | Boolean: true if syncPolicy exists |

### Annotation Key Normalization

Annotation keys are transformed for JSON compatibility:

**Examples**:
| Original Key | Normalized Key |
|--------------|----------------|
| `argocd.argoproj.io/sync-wave` | `syncWave` |
| `notifications.argoproj.io/subscribe.on-sync-succeeded` | `subscribeOnSyncSucceeded` |
| `my-custom-annotation` | `myCustomAnnotation` |
| `simple` | `simple` |

**Rules**:
1. Remove namespace prefix (e.g., `argocd.argoproj.io/`)
2. Split on `/` and take last segment
3. Convert kebab-case to camelCase
4. Convert snake_case to camelCase

---

## Validation and Error Handling

### Validation Rules

The parser enforces ArgoCD Application v1alpha1 schema rules:

✅ **Required Fields**:
- `apiVersion` must be `"argoproj.io/v1alpha1"`
- `kind` must be `"Application"`
- `metadata.name` must be non-empty
- `spec.project` (defaults to `"default"` if empty)
- `spec.source.repoURL` must be non-empty
- `spec.source.path` OR `spec.source.chart` must be specified
- `spec.destination.namespace` must be non-empty
- `spec.destination.server` OR `spec.destination.name` must be specified

❌ **Rejections**:
- Multi-document YAML files (only single-document manifests supported)
- Empty or whitespace-only required fields
- Missing required fields
- Invalid `apiVersion` or `kind`
- YAML syntax errors

### Error Messages

The parser provides detailed, actionable error messages:

#### Example 1: Missing Required Field

```
✗ app.yaml: spec.source.repoURL: Field required
```

#### Example 2: Empty Required Field

```
✗ app.yaml: metadata.name: Field cannot be empty or whitespace-only
```

#### Example 3: Multi-Document YAML

```
⊘ app.yaml: File contains 3 YAML documents. Expected exactly 1 document. Multi-document YAML files are not supported.
```

#### Example 4: Invalid API Version

```
✗ app.yaml: apiVersion: Invalid apiVersion 'argoproj.io/v1beta1'. Expected 'argoproj.io/v1alpha1'
```

#### Example 5: YAML Syntax Error

```
✗ app.yaml: YAML parsing error at line 12, column 5: expected <block end>, but found ':'
```

---

## JSON Output for Automation

Use `--json` flag for machine-readable output suitable for CI/CD pipelines:

```bash
argocd-parse --file app.yaml --output-dir ./output --json
```

**Output Format**:
```json
{
  "success": true,
  "results": [
    {
      "file": "/path/to/app.yaml",
      "status": "success",
      "output": "/path/to/output/app.json",
      "application": {
        "name": "example-app",
        "namespace": "argocd",
        "project": "default"
      }
    }
  ],
  "summary": {
    "total": 1,
    "successful": 1,
    "failed": 0,
    "skipped": 0
  }
}
```

**For Failed Parsing**:
```json
{
  "success": false,
  "results": [
    {
      "file": "/path/to/app.yaml",
      "status": "failed",
      "errors": [
        {
          "type": "MISSING_REQUIRED_FIELD",
          "field": "spec.source.repoURL",
          "message": "Field required"
        }
      ]
    }
  ],
  "summary": {
    "total": 1,
    "successful": 0,
    "failed": 1,
    "skipped": 0
  }
}
```

---

## Integration with Pipeline

The ArgoCD Parser is **Stage 2** in the 4-stage migration pipeline:

```
┌─────────┐    ┌────────┐    ┌──────────┐    ┌───────────┐
│ Scanner │ -> │ Parser │ -> │ Migrator │ -> │ Validator │
│ Stage 1 │    │ Stage 2│    │ Stage 3  │    │ Stage 4   │
└─────────┘    └────────┘    └──────────┘    └───────────┘
```

### Standalone Usage

```bash
# Parse without scanner (direct file input)
argocd-parse --file app.yaml --output-dir ./output
```

### Pipeline Integration

```bash
# Stage 1: Scan for YAML files
argocd-scan --directory ./apps --output scan-results.json

# Stage 2: Parse discovered files (using scan results)
argocd-parse --from-scan scan-results.json --output-dir ./parsed

# Stage 3 & 4: Migration and validation (future implementation)
# argocd-migrate --input ./parsed --output ./migrated
# argocd-validate --input ./migrated
```

---

## Troubleshooting

### Common Issues

#### Issue: "Output directory does not exist"

**Solution**: The parser automatically creates the output directory. If you see this error, check file permissions on the parent directory.

```bash
# Ensure parent directory is writable
ls -la $(dirname /path/to/output)
```

#### Issue: "Multi-document YAML not supported"

**Solution**: Split multi-document YAML files into separate files:

```bash
# Use csplit to split YAML documents
csplit -f app- apps.yaml '/^---$/' '{*}'
```

#### Issue: "Invalid apiVersion 'v1'"

**Solution**: Ensure the file is an ArgoCD Application manifest, not a standard Kubernetes resource:

```yaml
# Correct apiVersion
apiVersion: argoproj.io/v1alpha1
kind: Application

# Incorrect (standard Kubernetes)
apiVersion: v1
kind: Service
```

#### Issue: Parser skips all files with "Not an ArgoCD Application"

**Solution**: Verify files contain `kind: Application` and `apiVersion: argoproj.io/v1alpha1`. Use `--verbose` for detailed logging:

```bash
argocd-parse --directory ./apps --output-dir ./output --verbose
```

---

## Next Steps

After parsing ArgoCD manifests:

1. **Review JSON Output**: Inspect generated JSON files in the output directory
2. **Validate Transformations**: Check that field mappings are correct (especially cluster names and labels)
3. **Configure Defaults**: Create a `config.json` file to customize cluster mappings and default labels
4. **Pipeline Integration**: Feed JSON output into Stage 3 (Migrator) for further transformation
5. **Automation**: Use `--json` flag in CI/CD pipelines for automated processing

---

## Examples

### Example 1: Parse Single File with Config

```bash
argocd-parse \
  --file ./apps/guestbook.yaml \
  --output-dir ./output \
  --config ./parser-config.json
```

### Example 2: Batch Process with Quiet Mode

```bash
argocd-parse \
  --directory ./argocd-manifests \
  --output-dir ./json-output \
  --quiet
```

### Example 3: CI/CD Pipeline Integration

```bash
#!/bin/bash

# Parse ArgoCD manifests in CI
argocd-parse \
  --directory ./manifests \
  --output-dir ./build/parsed \
  --json > parse-results.json

# Check exit code
if [ $? -ne 0 ]; then
  echo "Parsing failed"
  cat parse-results.json | jq '.results[] | select(.status=="failed")'
  exit 1
fi

# Count successful parses
SUCCESS_COUNT=$(jq '.summary.successful' parse-results.json)
echo "Successfully parsed ${SUCCESS_COUNT} manifests"
```

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/org/app-migrator-claude/issues
- **Documentation**: See `specs/002-argocd-yaml-parser/` for detailed design docs

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-18 | Initial release |
