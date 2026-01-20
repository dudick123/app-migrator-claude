"""Unit tests for core YAML parsing logic."""

import pytest
import tempfile
from pathlib import Path
from parser.core import load_single_yaml_document, YAMLDocumentError


def test_load_single_yaml_document_success():
    """Test loading a valid single-document YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-app
spec:
  project: default
  source:
    repoURL: https://github.com/example/repo.git
    path: ./manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")
        temp_path = Path(f.name)

    try:
        document = load_single_yaml_document(temp_path)
        assert isinstance(document, dict)
        assert document["apiVersion"] == "argoproj.io/v1alpha1"
        assert document["kind"] == "Application"
        assert document["metadata"]["name"] == "test-app"
    finally:
        temp_path.unlink()


def test_load_single_yaml_document_multi_document():
    """Test that multi-document YAML is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app2
""")
        temp_path = Path(f.name)

    try:
        with pytest.raises(YAMLDocumentError) as exc_info:
            load_single_yaml_document(temp_path)
        assert "2 YAML documents" in str(exc_info.value)
        assert "Multi-document YAML files are not supported" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_load_single_yaml_document_empty_file():
    """Test that empty YAML file is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("")
        temp_path = Path(f.name)

    try:
        with pytest.raises(YAMLDocumentError) as exc_info:
            load_single_yaml_document(temp_path)
        assert "0 YAML documents" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_load_single_yaml_document_null_content():
    """Test that YAML file with null content is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("---\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(YAMLDocumentError) as exc_info:
            load_single_yaml_document(temp_path)
        assert "empty YAML document" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_load_single_yaml_document_non_dict():
    """Test that non-dict YAML content is rejected."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("- item1\n- item2\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(YAMLDocumentError) as exc_info:
            load_single_yaml_document(temp_path)
        assert "Expected YAML document to be a mapping" in str(exc_info.value)
    finally:
        temp_path.unlink()


def test_load_single_yaml_document_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_single_yaml_document(Path("/nonexistent/file.yaml"))
