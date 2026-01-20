"""Unit tests for field mapper logic."""

import pytest
from parser.mapper import normalize_annotation_key, transform_to_migration_output
from parser.models import (
    ArgoCDApplication,
    ArgoCDMetadata,
    ArgoCDSpec,
    ArgoCDSource,
    ArgoCDDestination,
)


class TestNormalizeAnnotationKey:
    """Tests for annotation key normalization."""

    def test_argocd_namespace_prefix(self):
        """Test removing argocd.argoproj.io/ prefix."""
        assert normalize_annotation_key("argocd.argoproj.io/sync-wave") == "syncWave"

    def test_notifications_namespace_prefix(self):
        """Test removing notifications.argoproj.io/ prefix."""
        assert (
            normalize_annotation_key(
                "notifications.argoproj.io/subscribe.on-sync-succeeded"
            )
            == "subscribeOnSyncSucceeded"
        )

    def test_custom_namespace_with_slash(self):
        """Test removing custom namespace prefix (takes last segment after /)."""
        assert normalize_annotation_key("custom.domain.io/my-key") == "myKey"

    def test_kebab_case_to_camel_case(self):
        """Test converting kebab-case to camelCase."""
        assert normalize_annotation_key("my-custom-key") == "myCustomKey"
        assert normalize_annotation_key("another-test-key") == "anotherTestKey"

    def test_snake_case_to_camel_case(self):
        """Test converting snake_case to camelCase."""
        assert normalize_annotation_key("my_custom_key") == "myCustomKey"

    def test_dot_notation_to_camel_case(self):
        """Test converting dot.notation to camelCase."""
        assert normalize_annotation_key("subscribe.on-sync") == "subscribeOnSync"

    def test_simple_key_unchanged(self):
        """Test that simple keys without special characters remain unchanged."""
        assert normalize_annotation_key("simple") == "simple"
        assert normalize_annotation_key("name") == "name"

    def test_single_word_keys(self):
        """Test single word keys."""
        assert normalize_annotation_key("test") == "test"


class TestTransformToMigrationOutput:
    """Tests for ArgoCD to migration output transformation."""

    def test_basic_transformation(self):
        """Test basic transformation with minimal required fields."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        output = transform_to_migration_output(app)

        assert output.metadata.name == "test-app"
        assert output.project == "default"
        assert output.source.repoURL == "https://github.com/org/repo.git"
        assert output.source.revision == "HEAD"
        assert output.source.manifestPath == "./manifests"
        assert output.destination.clusterName == "default"
        assert output.destination.namespace == "default"
        assert output.enableSyncPolicy is False

    def test_cluster_mapping(self):
        """Test cluster URL to name mapping."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        cluster_mappings = {
            "https://kubernetes.default.svc": "prod-cluster",
        }

        output = transform_to_migration_output(app, cluster_mappings=cluster_mappings)
        assert output.destination.clusterName == "prod-cluster"

    def test_destination_with_name(self):
        """Test using destination.name instead of server URL."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    name="staging-cluster",
                    namespace="default",
                ),
            ),
        )

        output = transform_to_migration_output(app)
        assert output.destination.clusterName == "staging-cluster"

    def test_default_labels(self):
        """Test adding default labels."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        default_labels = {
            "environment": "dev",
            "team": "platform",
        }

        output = transform_to_migration_output(app, default_labels=default_labels)
        assert output.metadata.labels == default_labels

    def test_manifest_labels_override_defaults(self):
        """Test that manifest labels take precedence over defaults."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(
                name="test-app",
                labels={"environment": "prod", "owner": "devops"},
            ),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        default_labels = {
            "environment": "dev",
            "team": "platform",
        }

        output = transform_to_migration_output(app, default_labels=default_labels)
        assert output.metadata.labels["environment"] == "prod"  # Manifest wins
        assert output.metadata.labels["team"] == "platform"  # Default added
        assert output.metadata.labels["owner"] == "devops"  # Manifest only

    def test_annotation_normalization(self):
        """Test that annotations are normalized."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(
                name="test-app",
                annotations={
                    "argocd.argoproj.io/sync-wave": "40",
                    "custom-annotation": "value",
                },
            ),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        output = transform_to_migration_output(app)
        assert "syncWave" in output.metadata.annotations
        assert output.metadata.annotations["syncWave"] == "40"
        assert "customAnnotation" in output.metadata.annotations
        assert output.metadata.annotations["customAnnotation"] == "value"

    def test_target_revision_renamed(self):
        """Test that targetRevision is renamed to revision."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    targetRevision="main",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        output = transform_to_migration_output(app)
        assert output.source.revision == "main"

    def test_directory_config_added_for_path(self):
        """Test that directory config is added when path is specified."""
        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
            ),
        )

        output = transform_to_migration_output(app)
        assert output.source.directory is not None
        assert output.source.directory.recurse is True

    def test_enable_sync_policy_true(self):
        """Test that enableSyncPolicy is true when syncPolicy is present."""
        from parser.models import ArgoCDSyncPolicy

        app = ArgoCDApplication(
            apiVersion="argoproj.io/v1alpha1",
            kind="Application",
            metadata=ArgoCDMetadata(name="test-app"),
            spec=ArgoCDSpec(
                source=ArgoCDSource(
                    repoURL="https://github.com/org/repo.git",
                    path="./manifests",
                ),
                destination=ArgoCDDestination(
                    server="https://kubernetes.default.svc",
                    namespace="default",
                ),
                syncPolicy=ArgoCDSyncPolicy(automated={"prune": True}),
            ),
        )

        output = transform_to_migration_output(app)
        assert output.enableSyncPolicy is True
