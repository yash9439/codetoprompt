"""Arg Parsers for CodeToPrompt."""

import argparse
from .version import __version__
from .config import load_config


def create_base_parser() -> argparse.ArgumentParser:
    """Creates a base parser with shared arguments like --version."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit."
    )
    return parser

def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for prompt generation."""
    base_parser = create_base_parser()
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Converts a codebase into a single, context-rich prompt for LLMs.",
        epilog=(
            "EXAMPLES:\n"
            "  # Generate a prompt from the current directory\n"
            "  codetoprompt .\n\n"
            "  # Generate a prompt in Markdown format\n"
            "  codetoprompt . -m\n\n"
            "  # Run a codebase analysis\n"
            "  codetoprompt analyse .\n\n"
            "  # Configure default settings\n"
            "  codetoprompt config\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        allow_abbrev=False,  # Disable abbreviated long options
        parents=[base_parser],
    )

    parser.add_argument(
        "directory",
        metavar="PATH",
        nargs="?",
        default=None,
        help="The path to the codebase directory to process (e.g., '.')."
    )
    parser.add_argument("--output", help="Save the prompt to a file instead of copying to clipboard.")
    parser.add_argument("--include", help="Comma-separated glob patterns of files to include.")
    parser.add_argument("--exclude", help="Comma-separated glob patterns of files to exclude.")
    parser.add_argument("--max-tokens", type=int, default=config.get("max_tokens"), help="Warn if token count exceeds this limit.")
    parser.add_argument("--tree-depth", type=int, default=config.get("tree_depth"), help="Maximum depth for the project structure tree.")

    # Add boolean flags with defaults from config
    rg_group = parser.add_mutually_exclusive_group()
    rg_group.add_argument("--respect-gitignore", action="store_true", dest="respect_gitignore", default=None, help="Respect .gitignore rules (overrides config).")
    rg_group.add_argument("--no-respect-gitignore", action="store_false", dest="respect_gitignore", help="Do not respect .gitignore rules (overrides config).")

    ln_group = parser.add_mutually_exclusive_group()
    ln_group.add_argument("--show-line-numbers", action="store_true", dest="show_line_numbers", default=None, help="Prepend line numbers to code (overrides config).")
    ln_group.add_argument("--no-show-line-numbers", action="store_false", dest="show_line_numbers", help="Do not show line numbers (overrides config).")

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively select which files to include in the prompt."
    )
    
    parser.add_argument("--compress", action="store_true", dest="compress", default=None, help="Use code compression to reduce prompt size.")
    ct_group = parser.add_mutually_exclusive_group()
    ct_group.add_argument("--count-tokens", action="store_true", dest="count_tokens", default=None, help="Count tokens in the prompt (overrides config).")
    ct_group.add_argument("--no-count-tokens", action="store_false", dest="count_tokens", help="Do not count tokens (improves speed, overrides config).")
    
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "-m", "--markdown",
        action="store_const",
        dest="output_format",
        const="markdown",
        help="Format output as Markdown with language hints."
    )
    format_group.add_argument(
        "-c", "--cxml",
        action="store_const",
        dest="output_format",
        const="cxml",
        help="Format output as Claude-friendly XML."
    )

    parser.set_defaults(
        respect_gitignore=config.get("respect_gitignore", True),
        show_line_numbers=config.get("show_line_numbers", False),
        compress=config.get("compress", False),
        count_tokens=config.get("count_tokens", True),
        output_format=config.get("output_format", "default"),
    )

    return parser

def create_analyse_parser() -> argparse.ArgumentParser:
    """Create a parser for the 'analyse' command."""
    base_parser = create_base_parser()
    config = load_config()
    parser = argparse.ArgumentParser(
        prog="codetoprompt analyse",
        description="Analyses a codebase and provides statistics on file types, sizes, and token counts.",
        parents=[base_parser],
        allow_abbrev=False,  # Disable abbreviated long options
    )
    parser.add_argument("directory", metavar="PATH", help="The path to the codebase directory to analyse.")
    parser.add_argument("--include", help="Comma-separated glob patterns of files to include.")
    parser.add_argument("--exclude", help="Comma-separated glob patterns of files to exclude.")
    parser.add_argument("--top-n", type=int, default=10, help="Number of items to show in top lists.")
    
    rg_group = parser.add_mutually_exclusive_group()
    rg_group.add_argument("--respect-gitignore", action="store_true", dest="respect_gitignore", default=None, help="Respect .gitignore rules (overrides config).")
    rg_group.add_argument("--no-respect-gitignore", action="store_false", dest="respect_gitignore", help="Do not respect .gitignore rules (overrides config).")

    parser.set_defaults(respect_gitignore=config.get("respect_gitignore", True))
    return parser


def create_config_parser() -> argparse.ArgumentParser:
    """Create a parser for the 'config' command."""
    base_parser = create_base_parser()
    parser = argparse.ArgumentParser(
        prog="codetoprompt config",
        description="View, reset, or interactively configure default settings.",
        parents=[base_parser],
        allow_abbrev=False,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--show", action="store_true", help="Show the current configuration.")
    group.add_argument("--reset", action="store_true", help="Reset the configuration to defaults.")
    return parser

