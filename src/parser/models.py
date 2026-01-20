"""Pydantic models for ArgoCD Application manifests and migration output."""

from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def non_empty_str(value: str) -> str:
    """Validate that a string is not empty or whitespace-only.

    Args:
        value: String to validate

    Returns:
        Stripped string value

    Raises:
        ValueError: If string is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValueError("Field cannot be empty or whitespace-only")
    return value.strip()


# Type alias for required non-empty strings
RequiredStr = Annotated[str, AfterValidator(non_empty_str)]


class ValidationError(BaseModel):
    """Validation error details for invalid manifests."""

    model_config = ConfigDict(frozen=True)

    error_type: str = Field(description="Error type code (e.g., MISSING_REQUIRED_FIELD)")
    field: str | None = Field(default=None, description="Field path that failed validation")
    message: str = Field(description="Human-readable error message")


class ParseResult(BaseModel):
    """Result of parsing a single ArgoCD manifest file."""

    model_config = ConfigDict(frozen=True)

    file_path: str = Field(description="Path to the source YAML file")
    status: str = Field(description="Parse status: success, failed, or skipped")
    output_path: str | None = Field(
        default=None, description="Path to output JSON file if successful"
    )
    application_name: str | None = Field(
        default=None,
        description="ArgoCD Application name from metadata.name"
    )
    errors: list[ValidationError] = Field(
        default_factory=list,
        description="List of validation errors if parsing failed"
    )


class BatchSummary(BaseModel):
    """Summary of batch processing operation."""

    model_config = ConfigDict(frozen=True)

    total: int = Field(description="Total number of files processed")
    successful: int = Field(description="Number of successfully parsed files")
    failed: int = Field(description="Number of files that failed parsing")
    skipped: int = Field(default=0, description="Number of files skipped")
    results: list[ParseResult] = Field(
        default_factory=list,
        description="Individual parse results for each file"
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


# Input models for ArgoCD Application v1alpha1

class ArgoCDMetadata(BaseModel):
    """Metadata section of ArgoCD Application manifest."""

    model_config = ConfigDict(extra="ignore")

    name: RequiredStr = Field(description="Application name (DNS-1123 subdomain)")
    namespace: str = Field(
        default="argocd",
        description="Namespace where Application resource is created",
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Custom labels")
    annotations: dict[str, str] = Field(default_factory=dict, description="Custom annotations")


class ArgoCDSource(BaseModel):
    """Source configuration for ArgoCD Application."""

    model_config = ConfigDict(extra="ignore")

    repoURL: RequiredStr = Field(description="Git or Helm repository URL")  # noqa: N815
    targetRevision: str = Field(  # noqa: N815
        default="HEAD",
        description="Git branch, tag, commit, or Helm chart version",
    )
    path: str | None = Field(
        default=None, description="Directory path within Git repository"
    )
    chart: str | None = Field(default=None, description="Helm chart name")

    def model_post_init(self, __context: Any) -> None:
        """Validate that either path or chart is specified, but not both."""
        if self.path is None and self.chart is None:
            raise ValueError("Either 'path' or 'chart' must be specified in source")
        if self.path is not None and self.chart is not None:
            raise ValueError("Cannot specify both 'path' and 'chart' in source")


class ArgoCDDestination(BaseModel):
    """Destination configuration for ArgoCD Application."""

    model_config = ConfigDict(extra="ignore")

    server: str | None = Field(default=None, description="Kubernetes API server URL")
    name: str | None = Field(default=None, description="Cluster name as defined in ArgoCD")
    namespace: RequiredStr = Field(description="Target namespace for deployment")

    def model_post_init(self, __context: Any) -> None:
        """Validate that either server or name is specified, but not both."""
        if self.server is None and self.name is None:
            raise ValueError("Either 'server' or 'name' must be specified in destination")
        if self.server is not None and self.name is not None:
            raise ValueError("Cannot specify both 'server' and 'name' in destination")


class ArgoCDSyncPolicy(BaseModel):
    """Sync policy configuration for ArgoCD Application."""

    model_config = ConfigDict(extra="ignore")

    automated: dict[str, Any] | None = Field(
        default=None, description="Automated sync configuration"
    )
    syncOptions: list[str] = Field(  # noqa: N815
        default_factory=list, description="Sync options"
    )
    retry: dict[str, Any] | None = Field(default=None, description="Retry configuration")


class ArgoCDSpec(BaseModel):
    """Spec section of ArgoCD Application manifest."""

    model_config = ConfigDict(extra="ignore")

    project: str = Field(default="default", description="ArgoCD project name")
    source: ArgoCDSource = Field(description="Source repository configuration")
    destination: ArgoCDDestination = Field(description="Deployment destination")
    syncPolicy: ArgoCDSyncPolicy | None = Field(  # noqa: N815
        default=None, description="Automated sync policy"
    )
    ignoreDifferences: list[dict[str, Any]] = Field(  # noqa: N815
        default_factory=list,
        description="Rules to ignore diffs"
    )
    info: list[dict[str, str]] = Field(default_factory=list, description="Additional metadata")


class ArgoCDApplication(BaseModel):
    """ArgoCD Application CRD v1alpha1 manifest model."""

    model_config = ConfigDict(extra="ignore")

    apiVersion: str = Field(description="API version")  # noqa: N815
    kind: str = Field(description="Resource kind")
    metadata: ArgoCDMetadata = Field(description="Kubernetes metadata")
    spec: ArgoCDSpec = Field(description="Application specification")

    def model_post_init(self, __context: Any) -> None:
        """Validate apiVersion and kind."""
        if self.apiVersion != "argoproj.io/v1alpha1":
            raise ValueError(
                f"Invalid apiVersion '{self.apiVersion}'. Expected 'argoproj.io/v1alpha1'"
            )
        if self.kind != "Application":
            raise ValueError(f"Invalid kind '{self.kind}'. Expected 'Application'")


# Output models for migration JSON

class OutputMetadata(BaseModel):
    """Metadata in migration output format."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Application name")
    annotations: dict[str, str] = Field(
        default_factory=dict,
        description="Normalized annotations (camelCase keys)"
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Labels including defaults")


class OutputDirectoryConfig(BaseModel):
    """Directory configuration for manifest discovery."""

    model_config = ConfigDict(frozen=True)

    recurse: bool = Field(default=True, description="Whether to recurse into subdirectories")


class OutputSource(BaseModel):
    """Source configuration in migration output format."""

    model_config = ConfigDict(frozen=True)

    repoURL: str = Field(description="Git or Helm repository URL")  # noqa: N815
    revision: str = Field(description="Git branch/tag/commit or Helm version")
    manifestPath: str | None = Field(  # noqa: N815
        default=None, description="Directory path within repository"
    )
    directory: OutputDirectoryConfig | None = Field(
        default=None,
        description="Directory configuration"
    )


class OutputDestination(BaseModel):
    """Destination configuration in migration output format."""

    model_config = ConfigDict(frozen=True)

    clusterName: str = Field(description="Target cluster name")  # noqa: N815
    namespace: str = Field(description="Target namespace")


class MigrationOutput(BaseModel):
    """Transformed ArgoCD Application data for migration tools."""

    model_config = ConfigDict(frozen=True)

    metadata: OutputMetadata = Field(description="Application metadata")
    project: str = Field(description="ArgoCD project name")
    source: OutputSource = Field(description="Source repository configuration")
    destination: OutputDestination = Field(description="Deployment destination")
    enableSyncPolicy: bool = Field(  # noqa: N815
        description="Whether automated sync policy is configured"
    )
