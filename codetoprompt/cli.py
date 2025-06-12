#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from .core import CodeToPrompt
from .utils import process_files


def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Convert code files to a prompt format."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing code files to process",
    )
    parser.add_argument(
        "--show-line-numbers",
        action="store_true",
        help="Show line numbers in the output",
    )
    parser.add_argument(
        "--respect-gitignore",
        action="store_true",
        help="Respect .gitignore rules",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: print to stdout)",
    )
    parser.add_argument(
        "--count-tokens",
        action="store_true",
        help="Count tokens in the generated prompt",
    )

    args = parser.parse_args(args)
    directory = Path(args.directory)

    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return 1

    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        return 1

    console = Console()

    # Show configuration summary
    config_panel = Panel(
        f"""Configuration:
Root Directory: {directory}
Include Patterns: ['*']
Exclude Patterns: []
Respect .gitignore: {args.respect_gitignore}
Show Line Numbers: {args.show_line_numbers}
Max Tokens: Unlimited
Copy to Clipboard: False""",
        title="CodeToPrompt",
        border_style="blue",
    )
    console.print(config_panel)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing files...", total=None)
            process_files(
                directory,
                show_line_numbers=args.show_line_numbers,
                respect_gitignore=args.respect_gitignore,
                output_file=args.output,
                count_tokens=args.count_tokens,
            )
        return 0
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
