"""Integration tests for CLI and end-to-end parsing."""

import json
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from parser.cli import app

runner = CliRunner()


@pytest.fixture
def valid_manifest_file():
    """Create a temporary valid ArgoCD Application manifest."""
    content = """
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "40"
  labels:
    environment: prod
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: main
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: guestbook
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()


@pytest.fixture
def config_file():
    """Create a temporary config file."""
    config = {
        "clusterMappings": {
            "https://kubernetes.default.svc": "prod-cluster"
        },
        "defaultLabels": {
            "team": "platform",
            "managed-by": "argocd-migrator"
        }
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        temp_path = Path(f.name)

    yield temp_path
    temp_path.unlink()


def test_parse_single_file_success(valid_manifest_file):
    """Test successful parsing of a single valid manifest."""
    with tempfile.TemporaryDirectory() as output_dir:
        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--output-dir", output_dir,
            ],
        )

        assert result.exit_code == 0
        assert "Successfully parsed: guestbook" in result.stdout

        # Verify JSON output was created
        output_file = Path(output_dir) / "guestbook.json"
        assert output_file.exists()

        # Verify JSON content
        with open(output_file, "r") as f:
            output = json.load(f)

        assert output["metadata"]["name"] == "guestbook"
        assert output["project"] == "default"
        assert output["source"]["repoURL"] == "https://github.com/argoproj/argocd-example-apps.git"
        assert output["source"]["revision"] == "main"
        assert output["source"]["manifestPath"] == "guestbook"
        assert output["destination"]["namespace"] == "guestbook"
        assert output["enableSyncPolicy"] is False


def test_parse_with_config(valid_manifest_file, config_file):
    """Test parsing with configuration file for cluster mappings and default labels."""
    with tempfile.TemporaryDirectory() as output_dir:
        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--output-dir", output_dir,
                "--config", str(config_file),
            ],
        )

        assert result.exit_code == 0

        # Verify cluster mapping was applied
        output_file = Path(output_dir) / "guestbook.json"
        with open(output_file, "r") as f:
            output = json.load(f)

        assert output["destination"]["clusterName"] == "prod-cluster"
        assert output["metadata"]["labels"]["team"] == "platform"
        assert output["metadata"]["labels"]["managed-by"] == "argocd-migrator"
        assert output["metadata"]["labels"]["environment"] == "prod"  # From manifest


def test_parse_missing_file():
    """Test error handling for missing input file."""
    with tempfile.TemporaryDirectory() as output_dir:
        result = runner.invoke(
            app,
            [
                "--file", "/nonexistent/file.yaml",
                "--output-dir", output_dir,
            ],
        )

        assert result.exit_code != 0


def test_parse_no_file_argument():
    """Test error when no file argument provided."""
    result = runner.invoke(app, ["--output-dir", "./output"])

    assert result.exit_code == 1
    assert "Must specify either --file or --directory" in result.stdout


def test_output_directory_creation(valid_manifest_file):
    """Test that output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "nested" / "output" / "dir"

        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--output-dir", str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert output_dir.exists()
        assert (output_dir / "guestbook.json").exists()


def test_annotation_normalization(valid_manifest_file):
    """Test that annotations are properly normalized in output."""
    with tempfile.TemporaryDirectory() as output_dir:
        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--output-dir", output_dir,
            ],
        )

        assert result.exit_code == 0

        output_file = Path(output_dir) / "guestbook.json"
        with open(output_file, "r") as f:
            output = json.load(f)

        # Check that argocd.argoproj.io/sync-wave was normalized to syncWave
        assert "syncWave" in output["metadata"]["annotations"]
        assert output["metadata"]["annotations"]["syncWave"] == "40"


def test_invalid_yaml_structure():
    """Test error handling for invalid YAML structure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("not: a: valid: yaml: structure:")
        temp_path = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(
                app,
                [
                    "--file", str(temp_path),
                    "--output-dir", output_dir,
                ],
            )

            assert result.exit_code == 1
            assert "Failed to parse" in result.stdout
    finally:
        temp_path.unlink()


def test_invalid_argocd_manifest():
    """Test error handling for non-ArgoCD manifest."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  selector:
    app: test
  ports:
    - port: 80
""")
        temp_path = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(
                app,
                [
                    "--file", str(temp_path),
                    "--output-dir", output_dir,
                ],
            )

            assert result.exit_code == 1
            assert "Failed to parse" in result.stdout
    finally:
        temp_path.unlink()


def test_parse_both_file_and_directory_error(valid_manifest_file):
    """Test error when both --file and --directory are specified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--directory", temp_dir,
                "--output-dir", "./output",
            ],
        )

        assert result.exit_code == 1
        assert "Cannot specify both --file and --directory" in result.stdout


def test_config_file_not_found(valid_manifest_file):
    """Test error handling when config file doesn't exist."""
    with tempfile.TemporaryDirectory() as output_dir:
        result = runner.invoke(
            app,
            [
                "--file", str(valid_manifest_file),
                "--output-dir", output_dir,
                "--config", "/nonexistent/config.json",
            ],
        )

        assert result.exit_code == 1
        assert "Config file not found" in result.stdout


def test_config_invalid_json(valid_manifest_file):
    """Test error handling when config file contains invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json {]")
        config_path = Path(f.name)

    try:
        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(
                app,
                [
                    "--file", str(valid_manifest_file),
                    "--output-dir", output_dir,
                    "--config", str(config_path),
                ],
            )

            assert result.exit_code == 1
            assert "Invalid JSON in config file" in result.stdout
    finally:
        config_path.unlink()


def test_batch_mode_json_output():
    """Test batch mode with JSON output format."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create valid manifest
        manifest = Path(temp_dir) / "app.yaml"
        manifest.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-app
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(
                app,
                [
                    "--directory", temp_dir,
                    "--output-dir", output_dir,
                    "--json",
                ],
            )

            assert result.exit_code == 0
            # Verify JSON output structure
            output = json.loads(result.stdout)
            assert "success" in output
            assert output["success"] is True
            assert "summary" in output
            assert output["summary"]["total"] == 1
            assert output["summary"]["successful"] == 1
            assert "results" in output
            assert len(output["results"]) == 1


def test_batch_mode_quiet():
    """Test batch mode with quiet flag suppresses progress output."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create valid manifest
        manifest = Path(temp_dir) / "app.yaml"
        manifest.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-app
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        with tempfile.TemporaryDirectory() as output_dir:
            result = runner.invoke(
                app,
                [
                    "--directory", temp_dir,
                    "--output-dir", output_dir,
                    "--quiet",
                ],
            )

            assert result.exit_code == 0
            # Quiet mode suppresses all output including progress and summary
            # Verify output file was created
            assert (Path(output_dir) / "test-app.json").exists()
