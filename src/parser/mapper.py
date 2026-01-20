"""Field mapping logic for transforming ArgoCD manifests to migration output format."""

from parser.models import (
    ArgoCDApplication,
    MigrationOutput,
    OutputDestination,
    OutputDirectoryConfig,
    OutputMetadata,
    OutputSource,
)


def normalize_annotation_key(key: str) -> str:
    """Normalize annotation/label keys for JSON output.

    Removes namespace prefixes and converts kebab-case to camelCase.

    Args:
        key: Original annotation/label key

    Returns:
        Normalized key in camelCase format

    Examples:
        >>> normalize_annotation_key("argocd.argoproj.io/sync-wave")
        'syncWave'
        >>> normalize_annotation_key("my-custom-key")
        'myCustomKey'
        >>> normalize_annotation_key("simple")
        'simple'
        >>> normalize_annotation_key("notifications.argoproj.io/subscribe.on-sync-succeeded")
        'subscribeOnSyncSucceeded'
    """
    # Remove ArgoCD namespace prefix
    if key.startswith("argocd.argoproj.io/"):
        key = key.replace("argocd.argoproj.io/", "")

    # Remove notifications namespace prefix
    if key.startswith("notifications.argoproj.io/"):
        key = key.replace("notifications.argoproj.io/", "")

    # Remove other common namespaces (take part after last slash)
    if "/" in key:
        key = key.split("/")[-1]

    # Convert kebab-case and snake_case to camelCase
    # First replace underscores with dashes for uniform handling
    key = key.replace("_", "-")

    # Split on dashes and dots
    parts = key.replace(".", "-").split("-")

    if len(parts) == 1:
        return parts[0]

    # First part stays lowercase, rest are capitalized
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def transform_to_migration_output(
    app: ArgoCDApplication,
    cluster_mappings: dict[str, str] | None = None,
    default_labels: dict[str, str] | None = None,
) -> MigrationOutput:
    """Transform ArgoCD Application manifest to migration output format.

    Args:
        app: Parsed ArgoCD Application manifest
        cluster_mappings: Optional mapping of server URLs to cluster names
        default_labels: Optional default labels to add if not present in manifest

    Returns:
        Transformed migration output

    Examples:
        >>> app = ArgoCDApplication(...)  # doctest: +SKIP
        >>> mappings = {"https://kubernetes.default.svc": "prod-cluster"}
        >>> output = transform_to_migration_output(  # doctest: +SKIP
        ...     app, cluster_mappings=mappings
        ... )
        >>> output.destination.clusterName  # doctest: +SKIP
        'prod-cluster'
    """
    cluster_mappings = cluster_mappings or {}
    default_labels = default_labels or {}

    # Normalize annotations
    normalized_annotations = {
        normalize_annotation_key(k): v for k, v in app.metadata.annotations.items()
    }

    # Merge default labels with manifest labels (manifest takes precedence)
    merged_labels = {**default_labels, **app.metadata.labels}

    # Map cluster name from server URL or use destination.name
    cluster_name: str
    if app.spec.destination.server:
        cluster_name = cluster_mappings.get(app.spec.destination.server, "default")
    elif app.spec.destination.name:
        cluster_name = app.spec.destination.name
    else:
        # This shouldn't happen due to Pydantic validation, but be defensive
        cluster_name = "default"

    # Create output models
    metadata = OutputMetadata(
        name=app.metadata.name,
        annotations=normalized_annotations,
        labels=merged_labels,
    )

    source = OutputSource(
        repoURL=app.spec.source.repoURL,
        revision=app.spec.source.targetRevision,
        manifestPath=app.spec.source.path,
        directory=(
            OutputDirectoryConfig(recurse=True) if app.spec.source.path else None
        ),
    )

    destination = OutputDestination(
        clusterName=cluster_name,
        namespace=app.spec.destination.namespace,
    )

    return MigrationOutput(
        metadata=metadata,
        project=app.spec.project,
        source=source,
        destination=destination,
        enableSyncPolicy=app.spec.syncPolicy is not None,
    )
