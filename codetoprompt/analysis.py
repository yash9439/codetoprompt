"""Analyse Feature for CodeToPrompt."""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from .core import CodeToPrompt
from .config import load_config, show_config_panel

def validate_directory(directory_path: str) -> Path:
    """
    Validate directory exists, is a directory, and return its absolute path.
    """
    path = Path(directory_path).resolve()
    if not path.exists():
        raise ValueError(f"Directory '{directory_path}' does not exist")
    if not path.is_dir():
        raise ValueError(f"'{directory_path}' is not a directory")
    return path

def run_analysis(args: argparse.Namespace, console: Console):
    """The main logic for analyzing a codebase."""
    config = load_config()
    include_patterns = [p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"]
    exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"]

    try:
        directory = validate_directory(args.directory)
        display_config = {
            "Root Directory": str(directory), "Include Patterns": include_patterns or ['*'], "Exclude Patterns": exclude_patterns or [],
            "Respect .gitignore": args.respect_gitignore,
        }
        show_config_panel(console, display_config, "Codebase Analysis")

        processor = CodeToPrompt(
            root_dir=str(directory), include_patterns=include_patterns, exclude_patterns=exclude_patterns,
            respect_gitignore=args.respect_gitignore,
        )

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TimeElapsedColumn(), console=console, transient=True,
        ) as progress:
            analysis_data = processor.analyse(progress, top_n=args.top_n)

        summary = analysis_data["overall"]
        summary_panel = Panel.fit(
            f"[bold]Total Files:[/bold] {summary['file_count']:,}\n"
            f"[bold]Total Lines:[/bold] {summary['total_lines']:,}\n"
            f"[bold]Total Tokens:[/bold] {summary['total_tokens']:,}",
            title="[cyan]Overall Project Summary[/cyan]", border_style="cyan"
        )
        console.print(summary_panel)

        if summary['file_count'] > 0:
            print_analysis_tables(console, analysis_data, args.top_n)

        return 0
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

def print_analysis_tables(console: Console, data: dict, top_n: int):
    """Prints the various analysis tables using rich."""
    ext_table = Table(title=f"Analysis by File Type (Top {top_n})", header_style="bold magenta")
    ext_table.add_column("Extension", style="green")
    ext_table.add_column("Files", justify="right")
    ext_table.add_column("Tokens", justify="right")
    ext_table.add_column("Lines", justify="right")
    ext_table.add_column("Avg Tokens/File", justify="right")
    for row in data["by_extension"]:
        avg = row['tokens'] / row['file_count']
        ext_table.add_row(row['extension'], f"{row['file_count']:,}", f"{row['tokens']:,}", f"{row['lines']:,}", f"{avg:,.0f}")
    console.print(ext_table)

    token_table = Table(title=f"Largest Files by Tokens (Top {top_n})", header_style="bold magenta")
    token_table.add_column("File Path", style="cyan")
    token_table.add_column("Tokens", justify="right")
    token_table.add_column("Lines", justify="right")
    for row in data["top_files_by_tokens"]:
        token_table.add_row(str(row['path']), f"{row['tokens']:,}", f"{row['lines']:,}")
    console.print(token_table)
