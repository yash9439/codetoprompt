import argparse
import sys


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Convert your codebase into a single LLM prompt"
    )
    parser.add_argument(
        "root_dir",
        help="Root directory of the codebase",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path",
    )
    parser.add_argument(
        "--include",
        "-i",
        help="Comma-separated list of file patterns to include",
        default="*",
    )
    parser.add_argument(
        "--exclude",
        "-e",
        help="Comma-separated list of file patterns to exclude",
        default="",
    )
    parser.add_argument(
        "--no-gitignore",
        help="Don't respect .gitignore rules",
        action="store_true",
    )
    parser.add_argument(
        "--no-line-numbers",
        help="Don't show line numbers",
        action="store_true",
    )
    parser.add_argument(
        "--max-tokens",
        help="Maximum number of tokens in the prompt",
        type=int,
    )
    parser.add_argument(
        "--no-copy",
        help="Don't copy prompt to clipboard",
        action="store_true",
    )

    args = parser.parse_args()

    # Print configuration
    print("╭────── CodeToPrompt ──────╮")
    print("│ Configuration:           │")
    print(f"│ Root Directory: {args.root_dir}        │")
    print(f"│ Include Patterns: {args.include.split(',')}  │")
    print(
        f"│ Exclude Patterns: {args.exclude.split(',') if args.exclude else []}     │"
    )
    print(f"│ Respect .gitignore: {not args.no_gitignore} │")
    print(f"│ Show Line Numbers: {not args.no_line_numbers}  │")
    print(f"│ Max Tokens: {args.max_tokens or 'Unlimited'}    │")
    print(f"│ Copy to Clipboard: {not args.no_copy} │")
    print("╰──────────────────────────╯")

    try:
        process_files(
            args.root_dir,
            include_patterns=args.include.split(","),
            exclude_patterns=args.exclude.split(",") if args.exclude else [],
            respect_gitignore=not args.no_gitignore,
            show_line_numbers=not args.no_line_numbers,
            max_tokens=args.max_tokens,
            copy_to_clipboard=not args.no_copy,
            output_file=args.output,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
