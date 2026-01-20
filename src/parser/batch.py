"""Batch processing functions for multiple ArgoCD manifests."""

from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from parser.core import parse_and_write
from parser.models import BatchSummary, ParseResult

console = Console()


def find_yaml_files(directory: Path, recursive: bool = True) -> list[Path]:
    """Find all YAML files in a directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories recursively

    Returns:
        List of YAML file paths (*.yaml and *.yml)

    Raises:
        NotADirectoryError: If path is not a directory
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    yaml_files: list[Path] = []

    if recursive:
        yaml_files.extend(directory.rglob("*.yaml"))
        yaml_files.extend(directory.rglob("*.yml"))
    else:
        yaml_files.extend(directory.glob("*.yaml"))
        yaml_files.extend(directory.glob("*.yml"))

    # Remove duplicates and sort
    return sorted(set(yaml_files))


def process_files_batch(
    files: list[Path],
    output_dir: Path,
    cluster_mappings: dict[str, str] | None = None,
    default_labels: dict[str, str] | None = None,
    show_progress: bool = True,
    progress_callback: Callable[[str, str], None] | None = None,
) -> BatchSummary:
    """Process multiple YAML files in batch mode.

    Args:
        files: List of YAML file paths to process
        output_dir: Output directory for JSON files
        cluster_mappings: Optional cluster URL to name mappings
        default_labels: Optional default labels
        show_progress: Whether to show progress bar
        progress_callback: Optional callback for progress updates (file_path, status)

    Returns:
        BatchSummary with results for all files
    """
    results: list[ParseResult] = []
    successful = 0
    failed = 0
    skipped = 0

    if show_progress and len(files) > 1:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing files...", total=len(files))

            for file_path in files:
                # Update progress description
                progress.update(task, description=f"Processing {file_path.name}")

                # Parse file (with error isolation)
                result = parse_and_write(
                    input_file=file_path,
                    output_dir=output_dir,
                    cluster_mappings=cluster_mappings,
                    default_labels=default_labels,
                )

                results.append(result)

                # Update counts
                if result.status == "success":
                    successful += 1
                    if progress_callback:
                        progress_callback(str(file_path), "success")
                    console.print(
                        f"[green]✓[/green] {file_path.name}: {result.application_name}"
                    )
                elif result.status == "failed":
                    failed += 1
                    if progress_callback:
                        progress_callback(str(file_path), "failed")
                    error_msg = result.errors[0].message if result.errors else "Unknown error"
                    console.print(f"[red]✗[/red] {file_path.name}: {error_msg}")
                else:
                    skipped += 1
                    if progress_callback:
                        progress_callback(str(file_path), "skipped")
                    console.print(f"[yellow]⊘[/yellow] {file_path.name}: Skipped")

                progress.advance(task)
    else:
        # Process without progress bar
        for file_path in files:
            result = parse_and_write(
                input_file=file_path,
                output_dir=output_dir,
                cluster_mappings=cluster_mappings,
                default_labels=default_labels,
            )

            results.append(result)

            if result.status == "success":
                successful += 1
                if progress_callback:
                    progress_callback(str(file_path), "success")
            elif result.status == "failed":
                failed += 1
                if progress_callback:
                    progress_callback(str(file_path), "failed")
            else:
                skipped += 1
                if progress_callback:
                    progress_callback(str(file_path), "skipped")

    return BatchSummary(
        total=len(files),
        successful=successful,
        failed=failed,
        skipped=skipped,
        results=results,
    )


def format_batch_summary(summary: BatchSummary, show_details: bool = True) -> None:
    """Format and print batch processing summary.

    Args:
        summary: BatchSummary with processing results
        show_details: Whether to show detailed per-file results
    """
    console.print("\n[bold]Batch Summary:[/bold]")
    console.print(f"  Total: {summary.total}")

    # Color-coded counts
    if summary.successful > 0:
        console.print(f"  [green]Successful: {summary.successful}[/green]")
    if summary.failed > 0:
        console.print(f"  [red]Failed: {summary.failed}[/red]")
    if summary.skipped > 0:
        console.print(f"  [yellow]Skipped: {summary.skipped}[/yellow]")

    # Success rate
    success_rate = summary.success_rate
    if success_rate >= 80:
        color = "green"
    elif success_rate >= 50:
        color = "yellow"
    else:
        color = "red"

    console.print(f"  [{color}]Success Rate: {success_rate:.1f}%[/{color}]")

    # Detailed errors (if requested and there are failures)
    if show_details and summary.failed > 0:
        console.print("\n[bold red]Failed Files:[/bold red]")
        for result in summary.results:
            if result.status == "failed":
                console.print(f"  • {result.file_path}")
                for error in result.errors:
                    if error.field:
                        console.print(f"    - {error.field}: {error.message}")
                    else:
                        console.print(f"    - {error.message}")
