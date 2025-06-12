#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

from .core import CodeToPrompt
from .config import load_config, save_config, get_config_path, reset_config


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for prompt generation."""
    config = load_config()

    parser = argparse.ArgumentParser(
        prog="codetoprompt",
        description="Converts a codebase into a single, context-rich prompt for LLMs.",
        epilog=(
            "EXAMPLES:\n"
            "  # Process the current directory\n"
            "  codetoprompt .\n\n"
            "  # Process a specific directory and save to a file\n"
            "  codetoprompt /path/to/project --output my_prompt.txt\n\n"
            "  # Process and exclude test files, respecting .gitignore\n"
            "  codetoprompt . --exclude \"tests/*,*.log\" --respect-gitignore\n\n"
            "CONFIGURATION:\n"
            "  To set your default preferences (e.g., to always respect .gitignore),\n"
            "  run the interactive wizard:\n"
            "    codetoprompt config\n\n"
            "  To view your current saved defaults:\n"
            "    codetoprompt config --show\n\n"
            "  To reset all settings to their original defaults:\n"
            "    codetoprompt config --reset"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "directory",
        metavar="PATH",
        help="The path to the codebase directory to process (e.g., '.')."
    )
    parser.add_argument("--output", help="Save the prompt to a file instead of copying to clipboard.")
    parser.add_argument("--include", help="Comma-separated glob patterns of files to include.")
    parser.add_argument("--exclude", help="Comma-separated glob patterns of files to exclude.")
    parser.add_argument("--max-tokens", type=int, default=config.get("max_tokens"), help="Warn if token count exceeds this limit.")
    parser.add_argument("--tree-depth", type=int, default=config.get("tree_depth"), help="Maximum depth for the project structure tree.")

    rg_group = parser.add_mutually_exclusive_group()
    rg_group.add_argument("--respect-gitignore", action="store_true", dest="respect_gitignore", default=None, help="Respect .gitignore rules (overrides config).")
    rg_group.add_argument("--no-respect-gitignore", action="store_false", dest="respect_gitignore", help="Do not respect .gitignore rules (overrides config).")

    ln_group = parser.add_mutually_exclusive_group()
    ln_group.add_argument("--show-line-numbers", action="store_true", dest="show_line_numbers", default=None, help="Prepend line numbers to code (overrides config).")
    ln_group.add_argument("--no-show-line-numbers", action="store_false", dest="show_line_numbers", help="Do not show line numbers (overrides config).")

    ct_group = parser.add_mutually_exclusive_group()
    ct_group.add_argument("--count-tokens", action="store_true", dest="count_tokens", default=None, help="Count tokens in the prompt (overrides config).")
    ct_group.add_argument("--no-count-tokens", action="store_false", dest="count_tokens", help="Do not count tokens (improves speed, overrides config).")

    parser.set_defaults(
        respect_gitignore=config["respect_gitignore"],
        show_line_numbers=config["show_line_numbers"],
        count_tokens=config["count_tokens"],
    )

    return parser


def run_config_logic(raw_args, console: Console):
    """Handle the 'config' command and its flags."""
    if "--reset" in raw_args:
        if reset_config():
            console.print("[green]✓ Configuration has been reset to defaults.[/green]")
        else:
            console.print("[yellow]No configuration file found. Already using defaults.[/yellow]")
    elif "--show" in raw_args:
        show_current_config(console)
    else:
        run_config_wizard(console)
    return 0


def show_current_config(console: Console):
    """Display the current configuration in a table."""
    config = load_config()
    table = Table(title="Current CodeToPrompt Defaults", title_style="bold cyan", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="green")
    table.add_column("Value")

    table.add_row("Respect .gitignore", str(config['respect_gitignore']))
    table.add_row("Show Line Numbers", str(config['show_line_numbers']))
    table.add_row("Count Tokens", str(config['count_tokens']))
    table.add_row("Tree Depth", str(config['tree_depth']))
    table.add_row("Max Tokens Warning", str(config.get('max_tokens') or "Unlimited"))
    table.add_row("Include Patterns", str(config.get('include_patterns') or "['*'] (All files)"))
    table.add_row("Exclude Patterns", str(config.get('exclude_patterns') or "[] (None)"))

    console.print(table)
    console.print(f"\n[dim]Config file location: {get_config_path()}[/dim]")


def run_config_wizard(console: Console):
    """Interactive wizard to set default configuration."""
    console.print(Panel.fit("[bold cyan]CodeToPrompt Configuration Wizard[/bold cyan]", border_style="blue"))
    console.print("Set your preferred defaults. Press Enter to keep the current value.")

    current_config = load_config()
    new_config = {}

    new_config["respect_gitignore"] = Confirm.ask(
        "Respect .gitignore files by default?", default=current_config.get("respect_gitignore")
    )
    new_config["show_line_numbers"] = Confirm.ask(
        "Show line numbers by default?", default=current_config.get("show_line_numbers")
    )
    new_config["count_tokens"] = Confirm.ask(
        "Count tokens by default (can be slow)?", default=current_config.get("count_tokens")
    )
    new_config["tree_depth"] = int(Prompt.ask(
        "Default directory tree depth?", default=str(current_config.get("tree_depth", 3))
    ))
    max_tokens_str = Prompt.ask(
        "Default maximum token warning limit (0 or Enter for none)?",
        default=str(current_config.get("max_tokens") or 0)
    )
    new_config["max_tokens"] = int(max_tokens_str) if max_tokens_str.isdigit() and int(max_tokens_str) > 0 else None
    include_str = Prompt.ask(
        "Default include patterns (comma-separated, Enter for all)",
        default=", ".join(current_config.get("include_patterns") or [])
    )
    new_config["include_patterns"] = [p.strip() for p in include_str.split(',') if p.strip()] or []
    exclude_str = Prompt.ask(
        "Default exclude patterns (comma-separated)",
        default=", ".join(current_config.get("exclude_patterns") or [])
    )
    new_config["exclude_patterns"] = [p.strip() for p in exclude_str.split(',') if p.strip()] or []

    save_config(new_config)
    console.print(f"\n[green]✓ Configuration saved to:[/] {get_config_path()}")


def run_prompt_generation(args: argparse.Namespace, console: Console):
    """The main logic for generating a prompt."""
    config = load_config()
    include_patterns = [p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"]
    exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"]

    try:
        directory = validate_directory(args.directory)
        display_config = {
            "directory": directory, "include_patterns": include_patterns, "exclude_patterns": exclude_patterns,
            "respect_gitignore": args.respect_gitignore, "show_line_numbers": args.show_line_numbers,
            "no_count_tokens": not args.count_tokens, "max_tokens": args.max_tokens, "tree_depth": args.tree_depth,
        }
        show_config_panel(console, display_config)

        processor = CodeToPrompt(
            root_dir=str(directory), include_patterns=include_patterns, exclude_patterns=exclude_patterns,
            respect_gitignore=args.respect_gitignore, show_line_numbers=args.show_line_numbers,
            max_tokens=args.max_tokens, tree_depth=args.tree_depth,
        )

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TimeElapsedColumn(), console=console,
        ) as progress:
            task = progress.add_task("Processing files...", total=None)
            processor.generate_prompt(progress)
            token_count_val = processor.get_token_count() if args.count_tokens else None

            clipboard_success = False
            if args.output:
                processor.save_to_file(args.output)
            else:
                 clipboard_success = processor.copy_to_clipboard()
            progress.update(task, completed=True)

        show_summary_panel(console, processor, token_count_val, args.output, clipboard_success)
        return 0
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def validate_directory(directory_path: str) -> Path:
    """Validate directory exists and is accessible."""
    directory = Path(directory_path)
    if not directory.exists():
        raise ValueError(f"Directory '{directory}' does not exist")
    if not directory.is_dir():
        raise ValueError(f"'{directory}' is not a directory")
    return directory


def show_config_panel(console: Console, config: dict):
    """Show configuration panel for a run."""
    config_text = (
        f"[bold]Configuration for this run:[/bold]\n"
        f"Root Directory: {config['directory']}\n"
        f"Include Patterns: {config['include_patterns'] or ['*']}\n"
        f"Exclude Patterns: {config['exclude_patterns'] or []}\n"
        f"Respect .gitignore: {config['respect_gitignore']}\n"
        f"Show Line Numbers: {config['show_line_numbers']}\n"
        f"Count Tokens: {not config['no_count_tokens']}\n"
        f"Max Tokens: {config['max_tokens'] or 'Unlimited'}\n"
        f"Tree Depth: {config['tree_depth']}"
    )
    panel = Panel.fit(config_text, title="CodeToPrompt", border_style="blue")
    console.print(panel)


def show_summary_panel(console: Console, processor: CodeToPrompt, token_count: int, output_file: str, clipboard_success: bool):
    """Show summary panel."""
    destination = "Clipboard" if not output_file else output_file
    if not output_file and not clipboard_success:
        destination = "stdout (clipboard copy failed)"

    summary_text = (
        f"[bold]Summary:[/bold]\n"
        f"Files Processed: {len(processor.processed_files)}\n"
        f"Total Tokens: {token_count if token_count is not None else 'Not counted'}\n"
        f"Output Destination: {destination}"
    )
    if not output_file:
         summary_text += f"\nCopied to Clipboard: {'Yes' if clipboard_success else 'No'}"

    panel = Panel.fit(summary_text, title="Processing Complete", border_style="green")
    console.print(panel)


def main(args=None):
    """Main CLI entry point."""
    raw_args = sys.argv[1:] if args is None else args
    console = Console()
    parser = create_parser()

    # Handle the 'config' command as a special case before parsing
    if raw_args and raw_args[0] == 'config':
        return run_config_logic(raw_args, console)

    # If no arguments are provided, show help and exit.
    if not raw_args:
        parser.print_help()
        return 0

    try:
        parsed_args = parser.parse_args(raw_args)
        return run_prompt_generation(parsed_args, console)
    except SystemExit as e:
        # This catches argparse's exit for -h/--help
        return e.code
    except Exception as e:
        console.print(f"[red]Error:[/red] An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())