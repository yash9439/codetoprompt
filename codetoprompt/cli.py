import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from .core import CodeToPrompt

def main(args=None):
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description="Convert your codebase into a single LLM prompt")
    parser.add_argument("directory", help="Directory to process")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--include", "-i", action="append", help="File patterns to include")
    parser.add_argument("--exclude", "-e", action="append", help="File patterns to exclude")
    parser.add_argument("--no-line-numbers", action="store_true", help="Disable line numbers")
    parser.add_argument("--max-tokens", type=int, help="Maximum number of tokens")
    
    args = parser.parse_args(args)
    
    console = Console()
    
    try:
        # Initialize processor
        processor = CodeToPrompt(
            args.directory,
            include_patterns=args.include,
            exclude_patterns=args.exclude,
            show_line_numbers=not args.no_line_numbers,
            max_tokens=args.max_tokens
        )
        
        # Process files with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Processing files...", total=None)
            prompt = processor.generate_prompt(progress)
            
        # Save to file or print to console
        if args.output:
            output_path = Path(args.output)
            processor.save_to_file(str(output_path))
            console.print(f"\n[green]✓[/green] Prompt saved to: {output_path}")
        else:
            console.print("\nGenerated Prompt:")
            console.print(prompt)
            
        return 0
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 