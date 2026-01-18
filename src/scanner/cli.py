"""CLI interface for YAML file scanner"""

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from scanner.core import (
    OutputFormat,
    ScanOptions,
    ScanResult,
    VerbosityLevel,
    scan_directory,
)

# Initialize Typer app and Rich console
app = typer.Typer(help="YAML File Scanner - Stage 1 of ArgoCD Application Migration Pipeline")
console = Console()
error_console = Console(stderr=True)


@app.command()
def scan(
    input_dir: Path = typer.Option(
        ...,
        "--input-dir",
        "-i",
        help="Directory to scan for YAML files (required)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Enable recursive subdirectory scanning",
    ),
    format: OutputFormat = typer.Option(
        "human",
        "--format",
        "-f",
        help="Output format: 'json' for JSON array, 'human' for formatted output",
    ),
    verbosity: VerbosityLevel = typer.Option(
        "info",
        "--verbosity",
        "-v",
        help="Output verbosity: 'quiet' (errors only), 'info' (summary), 'verbose' (detailed)",
    ),
) -> None:
    """
    Scan a directory for YAML files (.yaml and .yml extensions).

    Outputs discovered file paths to stdout and errors to stderr.
    Exit code 0 for success, 1 for errors.

    Examples:

        # Scan single directory
        argocd-scan --input-dir ./applications

        # Recursive scan with JSON output
        argocd-scan -i ./apps -r -f json

        # Verbose output
        argocd-scan -i ./apps -v verbose
    """
    try:
        # Create and validate options
        options = ScanOptions(
            input_dir=input_dir,
            recursive=recursive,
            format=format,
            verbosity=verbosity,
        )

        # Perform scan
        result = scan_directory(options)

        # Output results
        if format == "json":
            _output_json(result)
        else:
            _output_human(result, verbosity)

        # Output errors to stderr if any
        if result.has_errors:
            for error in result.errors:
                error_console.print(f"[red]Error:[/red] {error}")

        # Exit with appropriate code
        sys.exit(1 if result.has_errors else 0)

    except ValueError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


def _output_json(result: ScanResult) -> None:
    """
    Output scan results as JSON array to stdout.

    Args:
        result: Scan result to format
    """
    json_output = json.dumps(result.to_json_array(), indent=None)
    print(json_output)


def _output_human(result: ScanResult, verbosity: VerbosityLevel) -> None:
    """
    Output scan results in human-readable format using Rich.

    Args:
        result: Scan result to format
        verbosity: Verbosity level (quiet, info, verbose)
    """
    if verbosity == "quiet":
        # No output for quiet mode (errors are handled separately)
        return

    if verbosity == "info":
        # Summary output
        console.print(f"Found {result.count} YAML files")

    elif verbosity == "verbose":
        # Detailed output with table
        if result.count == 0:
            console.print("Found 0 YAML files")
        else:
            table = Table(title=f"Found {result.count} YAML files")
            table.add_column("File Path", style="cyan", no_wrap=False)

            for file_path in result.files:
                table.add_row(str(file_path))

            console.print(table)


if __name__ == "__main__":
    app()
