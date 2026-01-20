"""Unit tests for validation functions."""

import pytest
from pathlib import Path
from parser.validator import (
    is_argocd_application,
    validate_required_fields,
    validate_empty_null_fields,
    get_validation_error_summary,
)
from parser.core import load_single_yaml_document, YAMLDocumentError


class TestIsArgoCDApplication:
    """Tests for ArgoCD Application detection."""

    def test_valid_argocd_application(self):
        """Test detection of valid ArgoCD Application."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
        }
        assert is_argocd_application(document) is True

    def test_wrong_api_version(self):
        """Test rejection of wrong apiVersion."""
        document = {
            "apiVersion": "v1",
            "kind": "Application",
        }
        assert is_argocd_application(document) is False

    def test_wrong_kind(self):
        """Test rejection of wrong kind."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Service",
        }
        assert is_argocd_application(document) is False

    def test_missing_fields(self):
        """Test rejection when fields are missing."""
        assert is_argocd_application({}) is False
        assert is_argocd_application({"apiVersion": "argoproj.io/v1alpha1"}) is False


class TestValidateRequiredFields:
    """Tests for required field validation."""

    def test_all_required_fields_present(self):
        """Test that valid manifest has no missing fields."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test-app"},
            "spec": {
                "source": {
                    "repoURL": "https://github.com/org/repo.git",
                    "path": "./manifests",
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "default",
                },
            },
        }
        missing = validate_required_fields(document)
        assert missing == []

    def test_missing_api_version(self):
        """Test detection of missing apiVersion."""
        document = {"kind": "Application", "metadata": {"name": "test"}}
        missing = validate_required_fields(document)
        assert "apiVersion" in missing

    def test_missing_kind(self):
        """Test detection of missing kind."""
        document = {"apiVersion": "argoproj.io/v1alpha1", "metadata": {"name": "test"}}
        missing = validate_required_fields(document)
        assert "kind" in missing

    def test_missing_metadata(self):
        """Test detection of missing metadata section."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
        }
        missing = validate_required_fields(document)
        assert "metadata" in missing

    def test_missing_metadata_name(self):
        """Test detection of missing metadata.name."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git", "path": "./manifests"},
                "destination": {"server": "https://kubernetes.default.svc", "namespace": "default"},
            },
        }
        missing = validate_required_fields(document)
        assert "metadata.name" in missing

    def test_missing_spec(self):
        """Test detection of missing spec section."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
        }
        missing = validate_required_fields(document)
        assert "spec" in missing

    def test_missing_source(self):
        """Test detection of missing spec.source."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "default",
                }
            },
        }
        missing = validate_required_fields(document)
        assert "spec.source" in missing

    def test_missing_repo_url(self):
        """Test detection of missing spec.source.repoURL."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "source": {"path": "./manifests"},
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "default",
                },
            },
        }
        missing = validate_required_fields(document)
        assert "spec.source.repoURL" in missing

    def test_missing_path_and_chart(self):
        """Test detection when both path and chart are missing."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git"},
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": "default",
                },
            },
        }
        missing = validate_required_fields(document)
        assert any("path or" in field or "chart" in field for field in missing)

    def test_missing_destination(self):
        """Test detection of missing spec.destination."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "source": {
                    "repoURL": "https://github.com/org/repo.git",
                    "path": "./manifests",
                }
            },
        }
        missing = validate_required_fields(document)
        assert "spec.destination" in missing

    def test_missing_destination_namespace(self):
        """Test detection of missing spec.destination.namespace."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "source": {
                    "repoURL": "https://github.com/org/repo.git",
                    "path": "./manifests",
                },
                "destination": {"server": "https://kubernetes.default.svc"},
            },
        }
        missing = validate_required_fields(document)
        assert "spec.destination.namespace" in missing

    def test_missing_destination_server_and_name(self):
        """Test detection when both server and name are missing."""
        document = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {"name": "test"},
            "spec": {
                "source": {
                    "repoURL": "https://github.com/org/repo.git",
                    "path": "./manifests",
                },
                "destination": {"namespace": "default"},
            },
        }
        missing = validate_required_fields(document)
        assert any("server or" in field or "name" in field for field in missing)


class TestValidateEmptyNullFields:
    """Tests for empty/null field validation."""

    def test_no_empty_fields(self):
        """Test that valid manifest has no empty fields."""
        document = {
            "metadata": {"name": "test-app"},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git"},
                "destination": {"namespace": "default"},
            },
        }
        empty = validate_empty_null_fields(document)
        assert empty == []

    def test_empty_string_name(self):
        """Test detection of empty string in metadata.name."""
        document = {
            "metadata": {"name": ""},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git"},
                "destination": {"namespace": "default"},
            },
        }
        empty = validate_empty_null_fields(document)
        assert "metadata.name" in empty

    def test_whitespace_only_name(self):
        """Test detection of whitespace-only metadata.name."""
        document = {
            "metadata": {"name": "   "},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git"},
                "destination": {"namespace": "default"},
            },
        }
        empty = validate_empty_null_fields(document)
        assert "metadata.name" in empty

    def test_empty_repo_url(self):
        """Test detection of empty repoURL."""
        document = {
            "metadata": {"name": "test"},
            "spec": {
                "source": {"repoURL": ""},
                "destination": {"namespace": "default"},
            },
        }
        empty = validate_empty_null_fields(document)
        assert "spec.source.repoURL" in empty

    def test_empty_namespace(self):
        """Test detection of empty destination.namespace."""
        document = {
            "metadata": {"name": "test"},
            "spec": {
                "source": {"repoURL": "https://github.com/org/repo.git"},
                "destination": {"namespace": ""},
            },
        }
        empty = validate_empty_null_fields(document)
        assert "spec.destination.namespace" in empty


class TestGetValidationErrorSummary:
    """Tests for validation error summary formatting."""

    def test_empty_error_list(self):
        """Test formatting of empty error list."""
        summary = get_validation_error_summary([])
        assert summary == "No validation errors"

    def test_single_error(self):
        """Test formatting of single error."""
        errors = [{"loc": ("metadata", "name"), "msg": "Field required"}]
        summary = get_validation_error_summary(errors)
        assert "metadata.name" in summary
        assert "Field required" in summary

    def test_multiple_errors(self):
        """Test formatting of multiple errors."""
        errors = [
            {"loc": ("metadata", "name"), "msg": "Field required"},
            {"loc": ("spec", "source", "repoURL"), "msg": "Field required"},
        ]
        summary = get_validation_error_summary(errors)
        assert "metadata.name" in summary
        assert "spec.source.repoURL" in summary
        assert ";" in summary  # Multiple errors separated by semicolon


class TestInvalidManifestFixtures:
    """Tests using invalid manifest fixtures."""

    def test_multi_document_yaml_rejected(self):
        """Test that multi-document YAML is rejected."""
        fixture_path = Path("tests/fixtures/parser/invalid-manifests/multi-document.yaml")
        with pytest.raises(YAMLDocumentError) as exc_info:
            load_single_yaml_document(fixture_path)
        assert "2 YAML documents" in str(exc_info.value)
        assert "Multi-document" in str(exc_info.value)

    def test_malformed_yaml_syntax(self):
        """Test that malformed YAML syntax is rejected."""
        fixture_path = Path("tests/fixtures/parser/invalid-manifests/malformed-syntax.yaml")
        with pytest.raises(Exception):  # yaml.YAMLError or similar
            load_single_yaml_document(fixture_path)
