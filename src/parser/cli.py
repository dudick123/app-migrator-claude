"""CLI interface for ArgoCD YAML Parser."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from parser.batch import find_yaml_files, format_batch_summary, process_files_batch
from parser.core import parse_and_write

app = typer.Typer(
    name="argocd-parse",
    help="Parse ArgoCD Application manifests and transform to migration JSON format",
    no_args_is_help=True,
)

console = Console()


def load_config(config_path: Path) -> dict[str, dict[str, str]]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary with clusterMappings and defaultLabels

    Raises:
        typer.Exit: If config file is invalid
    """
    try:
        with open(config_path) as f:
            config: dict[str, dict[str, str]] = json.load(f)
        return config
    except FileNotFoundError:
        console.print(f"[red]Error: Config file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in config file: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def parse(
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            help=(
                "Path to ArgoCD Application YAML file to parse "
                "(mutually exclusive with --directory)"
            ),
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    directory: Annotated[
        Path | None,
        typer.Option(
            "--directory",
            "-d",
            help=(
                "Directory containing ArgoCD manifests to process "
                "(mutually exclusive with --file)"
            ),
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for JSON files (will be created if it doesn't exist)",
            resolve_path=True,
        ),
    ] = Path("./output"),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration JSON file (for cluster mappings and default labels)",
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress progress output (batch mode only)",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output results in JSON format for automation (batch mode only)",
        ),
    ] = False,
) -> None:
    """Parse ArgoCD Application manifest(s) and generate migration JSON output.

    Validates input YAML against ArgoCD Application v1alpha1 schema and
    transforms to a normalized JSON format for migration planning.

    Single file mode:
        argocd-parse --file app.yaml --output-dir ./output

    Batch directory mode:
        argocd-parse --directory ./manifests --output-dir ./output

    With configuration:
        argocd-parse --file app.yaml --output-dir ./output --config config.json

    JSON output for automation:
        argocd-parse --directory ./manifests --output-dir ./output --json
    """
    # Validate mutual exclusion
    if file and directory:
        console.print("[red]Error: Cannot specify both --file and --directory[/red]")
        raise typer.Exit(1)

    if not file and not directory:
        console.print("[red]Error: Must specify either --file or --directory[/red]")
        raise typer.Exit(1)

    # Load configuration if provided
    cluster_mappings = None
    default_labels = None

    if config:
        config_data = load_config(config)
        cluster_mappings = config_data.get("clusterMappings")
        default_labels = config_data.get("defaultLabels")

    # Single file mode
    if file:
        if not quiet:
            console.print(f"[cyan]Parsing:[/cyan] {file}")

        result = parse_and_write(
            input_file=file,
            output_dir=output_dir,
            cluster_mappings=cluster_mappings,
            default_labels=default_labels,
        )

        # Display results
        if result.status == "success":
            if not quiet:
                console.print(f"[green]✓[/green] Successfully parsed: {result.application_name}")
                console.print(f"[dim]Output:[/dim] {result.output_path}")
        else:
            console.print(f"[red]✗[/red] Failed to parse: {file}")
            if result.errors:
                console.print("\n[red]Errors:[/red]")
                for error in result.errors:
                    if error.field:
                        console.print(f"  • {error.field}: {error.message}")
                    else:
                        console.print(f"  • {error.message}")
            raise typer.Exit(1)

    # Batch directory mode
    elif directory:
        # Find all YAML files
        try:
            yaml_files = find_yaml_files(directory, recursive=True)
        except NotADirectoryError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        if not yaml_files:
            console.print(f"[yellow]No YAML files found in {directory}[/yellow]")
            raise typer.Exit(0)

        if not quiet and not json_output:
            console.print(f"[cyan]Found {len(yaml_files)} YAML file(s) in {directory}[/cyan]\n")

        # Process batch
        summary = process_files_batch(
            files=yaml_files,
            output_dir=output_dir,
            cluster_mappings=cluster_mappings,
            default_labels=default_labels,
            show_progress=not quiet and not json_output,
        )

        # Output results
        if json_output:
            # Machine-readable JSON output
            output = {
                "success": summary.failed == 0,
                "summary": {
                    "total": summary.total,
                    "successful": summary.successful,
                    "failed": summary.failed,
                    "skipped": summary.skipped,
                    "success_rate": round(summary.success_rate, 1),
                },
                "results": [
                    {
                        "file": result.file_path,
                        "status": result.status,
                        "output": result.output_path,
                        "application_name": result.application_name,
                        "errors": [
                            {
                                "type": error.error_type,
                                "field": error.field,
                                "message": error.message,
                            }
                            for error in result.errors
                        ] if result.errors else [],
                    }
                    for result in summary.results
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable summary
            if not quiet:
                format_batch_summary(summary, show_details=True)

        # Exit with appropriate code
        if summary.failed > 0:
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
