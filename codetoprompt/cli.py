"""CLI Functionality for CodeToPrompt."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .core import CodeToPrompt
from .config import load_config, show_config_panel, run_config_command
from .interactive import FileSelectorApp
from .analysis import validate_directory, run_analysis
from .arg_parser import create_main_parser, create_config_parser, create_analyse_parser
from .utils import is_url
from . import remote 

def run_prompt_generation(args: argparse.Namespace, console: Console):
    """The main logic for generating a prompt."""
    if not args.target:
        console.print("[red]Error:[/red] A path or URL is required for prompt generation.")
        create_main_parser().print_help()
        return 1

    is_remote_target = is_url(args.target)
    config = load_config() 

    # Check for incompatible flags with remote targets
    if is_remote_target:
        incompatible_flags = []
        if args.interactive: incompatible_flags.append("--interactive")
        if args.respect_gitignore is False: incompatible_flags.append("--no-respect-gitignore")
        if args.compress: incompatible_flags.append("--compress")
        if incompatible_flags:
            console.print(f"[red]Error:[/red] The flag(s) {', '.join(incompatible_flags)} cannot be used with a URL target.")
            return 1
    else:
        # Local path validation
        try:
            directory = validate_directory(args.target)
            args.target = str(directory)  # Use the validated, resolved path
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            return 1

    explicit_files = None
    if not is_remote_target and args.interactive:
        # The scanner now holds all the filtering logic.
        scanner = CodeToPrompt(
            target=args.target,
            include_patterns=[p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"],
            exclude_patterns=[p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"],
            respect_gitignore=args.respect_gitignore,
        )
        app = FileSelectorApp(root_path=Path(args.target), scanner=scanner)
        selected_files = app.run()

        if selected_files is None:
            console.print("\n[yellow]Interactive selection cancelled.[/yellow]")
            return 0
        if not selected_files:
            console.print("\n[yellow]No files were selected.[/yellow]")
            return 0
        explicit_files = selected_files

    if is_remote_target:
        display_config = {
            "URL Target": args.target,
            "Output Format": args.output_format,
            "Max Tokens": args.max_tokens or "Unlimited",
        }
        show_config_panel(console, display_config, "CodeToPrompt (Remote)")
    else:
        include_patterns = [p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"]
        exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"]
        display_config = {
            "Root Directory": args.target, "Include Patterns": include_patterns or ['*'], "Exclude Patterns": exclude_patterns or [],
            "Respect .gitignore": args.respect_gitignore, "Show Line Numbers": args.show_line_numbers,
            "Count Tokens": args.count_tokens, "Compress Code": args.compress, "Max Tokens": args.max_tokens or "Unlimited", "Tree Depth": args.tree_depth,
            "Output Format": args.output_format, "Interactive Mode": args.interactive,
        }
        show_config_panel(console, display_config, "CodeToPrompt (Local)")

    try:
        processor = CodeToPrompt(
            target=args.target,
            include_patterns=[p.strip() for p in args.include.split(',')] if args.include else None,
            exclude_patterns=[p.strip() for p in args.exclude.split(',')] if args.exclude else None,
            compress=args.compress,
            respect_gitignore=args.respect_gitignore, show_line_numbers=args.show_line_numbers,
            max_tokens=args.max_tokens, tree_depth=args.tree_depth,
            output_format=args.output_format,
            explicit_files=explicit_files,
        )

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TimeElapsedColumn(), console=console, transient=True,
        ) as progress:
            prompt = processor.generate_prompt(progress)

        clipboard_success = False
        if args.output:
            processor.save_to_file(args.output)
        else:
            clipboard_success = processor.copy_to_clipboard()
        
        show_summary_panel(console, processor, args.count_tokens, args.output, clipboard_success)
        return 0
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def show_summary_panel(console: Console, processor: CodeToPrompt, count_tokens_enabled: bool, output_file: str, clipboard_success: bool):
    """Show summary panel for prompt generation."""
    destination = "Clipboard" if not output_file else output_file
    if not output_file and not clipboard_success:
        destination = "stdout (clipboard copy failed)"
    
    token_count_str = f"{processor.get_token_count():,}" if count_tokens_enabled else 'Not counted'
    
    file_count = len(processor.processed_files)
    if file_count == 1 and processor.is_remote and remote.get_url_type(processor.target) != "github":
        summary_text = (
            f"[bold]Summary:[/bold]\n"
            f"Source Type: {remote.get_url_type(processor.target).capitalize()}\n"
            f"Total Tokens: {token_count_str}\n"
            f"Output Destination: {destination}"
        )
    else:
        summary_text = (
            f"[bold]Summary:[/bold]\n"
            f"Files Processed: {file_count}\n"
            f"Total Tokens: {token_count_str}\n"
            f"Output Destination: {destination}"
        )

    if not output_file:
         summary_text += f"\nCopied to Clipboard: {'Yes' if clipboard_success else 'No'}"

    if count_tokens_enabled and processor.processed_files and file_count > 1:
        top_files = processor.get_top_files_by_tokens(3)
        if top_files:
            summary_text += "\n\n[bold]Top 3 Files by Tokens:[/bold]"
            for file_info in top_files:
                summary_text += f"\n  - {file_info['path']} ({file_info['tokens']:,} tokens)"

        top_extensions = processor.get_top_extensions_by_tokens(5)
        if top_extensions:
            summary_text += "\n\n[bold]Top 5 Extensions by Tokens:[/bold]"
            for ext_info in top_extensions:
                summary_text += f"\n  - {ext_info['extension']} ({ext_info['tokens']:,} tokens)"

    panel = Panel.fit(summary_text, title="Processing Complete", border_style="green")
    console.print(panel)


def main(args=None):
    """Main CLI entry point."""
    raw_args = sys.argv[1:] if args is None else args
    console = Console()

    try:
        # Special handling for subcommands
        if raw_args:
            command = raw_args[0]
            if command == 'config':
                parser = create_config_parser()
                parsed_args = parser.parse_args(raw_args[1:])
                return run_config_command(parsed_args, console)
            if command == 'analyse':
                parser = create_analyse_parser()
                parsed_args = parser.parse_args(raw_args[1:])
                return run_analysis(parsed_args, console)

        # Default to prompt generation if no subcommand is found
        parser = create_main_parser()
        if not raw_args:
            parser.print_help()
            return 0
        
        parsed_args = parser.parse_args(raw_args)
        return run_prompt_generation(parsed_args, console)

    except SystemExit as e:
        # This catches argparse's exit for -h/--help or an error from ANY parser
        return e.code
    except Exception as e:
        console.print(f"[red]Error:[/red] An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())