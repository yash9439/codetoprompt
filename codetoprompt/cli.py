import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import print as rprint
from .core import CodeToPrompt

def main():
    parser = argparse.ArgumentParser(description="Convert your codebase into a single LLM prompt")
    parser.add_argument("root_dir", help="Root directory of the codebase")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--include", "-i", help="Comma-separated list of file patterns to include")
    parser.add_argument("--exclude", "-e", help="Comma-separated list of file patterns to exclude")
    parser.add_argument("--no-gitignore", action="store_true", help="Don't respect .gitignore rules")
    parser.add_argument("--no-line-numbers", action="store_true", help="Don't show line numbers")
    parser.add_argument("--max-tokens", type=int, help="Maximum number of tokens in the prompt")
    parser.add_argument("--no-copy", action="store_true", help="Don't copy prompt to clipboard")
    
    args = parser.parse_args()
    console = Console()
    
    try:
        # Validate root directory
        root_dir = Path(args.root_dir)
        if not root_dir.exists():
            console.print(f"[red]Error: Directory '{args.root_dir}' does not exist[/red]")
            return 1
        if not root_dir.is_dir():
            console.print(f"[red]Error: '{args.root_dir}' is not a directory[/red]")
            return 1
            
        # Process include/exclude patterns
        include_patterns = args.include.split(",") if args.include else None
        exclude_patterns = args.exclude.split(",") if args.exclude else None
        
        # Print configuration
        console.print(Panel.fit(
            f"[bold]Configuration:[/bold]\n"
            f"Root Directory: {root_dir}\n"
            f"Include Patterns: {include_patterns or ['*']}\n"
            f"Exclude Patterns: {exclude_patterns or []}\n"
            f"Respect .gitignore: {not args.no_gitignore}\n"
            f"Show Line Numbers: {not args.no_line_numbers}\n"
            f"Max Tokens: {args.max_tokens or 'Unlimited'}\n"
            f"Copy to Clipboard: {not args.no_copy}",
            title="CodeToPrompt",
            border_style="blue"
        ))
        
        # Initialize processor
        processor = CodeToPrompt(
            root_dir=str(root_dir),
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            respect_gitignore=not args.no_gitignore,
            show_line_numbers=not args.no_line_numbers,
            max_tokens=args.max_tokens
        )
        
        # Check clipboard requirements before starting progress bars
        clipboard_success = False
        if not args.no_copy:
            clipboard_success = processor.copy_to_clipboard()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Add all tasks upfront
            git_task = progress.add_task("Getting git information...", total=None)
            tree_task = progress.add_task("Building file tree...", total=None)
            files_task = progress.add_task("Finding files...", total=None)
            process_task = progress.add_task("Processing files...", total=None)
            save_task = progress.add_task("Saving to file...", total=None) if args.output else None
            
            # Generate prompt
            prompt = processor.generate_prompt()
            
            # Update progress for completed tasks
            progress.update(git_task, completed=True)
            progress.update(tree_task, completed=True)
            progress.update(files_task, completed=True)
            progress.update(process_task, completed=True)
            
            # # Print the generated prompt to the console
            # console.print("\n[bold]Generated Prompt:[/bold]\n")
            # console.print(prompt)
            
            # Save to file if specified
            if args.output:
                processor.save_to_file(args.output)
                progress.update(save_task, completed=True)
                console.print(f"[green]✓ Prompt saved to {args.output}[/green]")
            
        # Print summary
        console.print(Panel.fit(
            f"[bold]Summary:[/bold]\n"
            f"Total Tokens: {len(processor.tokenizer.encode(prompt)):,}\n"
            f"Output File: {args.output or 'None'}\n"
            f"Copied to Clipboard: {'Yes' if clipboard_success else 'No'}",
            title="Processing Complete",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 