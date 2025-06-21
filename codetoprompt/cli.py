#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import Set, List, Optional, Iterable

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from .core import CodeToPrompt
from .config import load_config, save_config, get_config_path, reset_config
from .version import __version__

try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Tree, Static
    from textual.widgets.tree import TreeNode
    from textual.events import Key
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False


# --- New Textual TUI for Interactive Mode ---

if HAS_TEXTUAL:
    class SelectableTree(Tree):
        """
        A custom Tree widget that overrides key-press behavior to create a
        more intuitive selection interface, including arrow and WASD navigation.
        """
        def on_key(self, event: Key) -> None:
            """Process key events to handle selection, confirmation, and navigation."""
            # Toggle selection with space
            if event.key == "space":
                self.app.action_toggle_selection()
                event.stop()
                return

            # Confirm selection with enter
            if event.key == "enter":
                self.app.action_confirm_selection()
                event.stop()
                return

            # Collapse folder with left arrow
            if event.key in ("left",):
                tree = self.app.query_one(Tree)
                node = tree.cursor_node
                if node and node.data.get("is_dir"):
                    node.collapse()
                    tree.refresh()
                event.stop()
                return

            # Expand folder with right arrow
            if event.key in ("right",):
                tree = self.app.query_one(Tree)
                node = tree.cursor_node
                if node and node.data.get("is_dir"):
                    node.expand()
                    tree.refresh()
                event.stop()
                return
                
            # WASD navigation:
            tree = self.app.query_one(Tree)
            node = tree.cursor_node
            if event.key == "w":            
                tree = self.app.query_one(Tree)
                # call the method on the Tree instance
                getattr(tree, "action_cursor_up")()
                tree.refresh()
                event.stop()
                return
            
            if event.key == "s":
                tree = self.app.query_one(Tree)
                # call the method on the Tree instance
                getattr(tree, "action_cursor_down")()
                tree.refresh()
                event.stop()
                return

            if event.key == "a":
                # treat 'a' like left arrow: collapse
                if node and node.data.get("is_dir"):
                    node.collapse()
                    tree.refresh()
                event.stop()
                return

            if event.key == "d":
                # treat 'd' like right arrow: expand
                if node and node.data.get("is_dir"):
                    node.expand()
                    tree.refresh()
                event.stop()
                return

    class FileSelectorApp(App):
        """A Textual TUI for interactively selecting files and directories."""

        BINDINGS = [
            ("q", "quit", "Quit"),
        ]

        def __init__(self, root_path: Path, candidate_files: Set[Path]):
            super().__init__()
            self.root_path = root_path
            self.candidate_files = candidate_files
            self.selected_paths = set()

        def compose(self) -> ComposeResult:
            yield Header()
            yield Static(
                "Navigate: [b]↑/↓/w/s[/b] | Expand/Collapse: [b]←/→/a/d[/b] | Toggle Select: [b]Space[/b] | Confirm: [b]Enter[/b]\n"
                "[green]✓[/green] = All selected | [yellow]-[/yellow] = Some selected | [grey50]◦[/grey50] = None selected",
                id="instructions",
            )
            yield SelectableTree(self.root_path.name, id="file_tree")
            yield Footer()

        def on_mount(self) -> None:
            """Called when the app is mounted. Sets up the UI."""
            self.query_one("#instructions").styles.text_align = "center"
            self.query_one("#instructions").styles.padding = (0, 1)

            tree = self.query_one(Tree)
            tree.root.data = {"path": self.root_path, "is_dir": True, "selected": False}
            self._populate_tree(self.root_path, tree.root)
            self._update_all_labels()
            tree.root.expand()

        def _populate_tree(self, dir_path: Path, node: TreeNode) -> None:
            """Recursively populates the tree with directories and candidate files."""
            paths = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))

            for path in paths:
                if path.is_dir():
                    if any(p.is_relative_to(path) for p in self.candidate_files):
                        child_node = node.add(path.name, data={"path": path, "is_dir": True, "selected": False})
                        self._populate_tree(path, child_node)
                elif path in self.candidate_files:
                    node.add_leaf(path.name, data={"path": path, "is_dir": False, "selected": False})

        def _is_fully_selected(self, node: TreeNode) -> bool:
            """Recursively checks if a node and all its descendants are marked as selected."""
            if not node.data["selected"]:
                return False
            if node.data["is_dir"]:
                return all(self._is_fully_selected(child) for child in node.children)
            return True

        def _set_node_and_children_selected(self, node: TreeNode, selected: bool):
            """Recursively sets the 'selected' data for a node and all its children."""
            node.data["selected"] = selected
            if node.data["is_dir"]:
                for child in node.children:
                    self._set_node_and_children_selected(child, selected)

        def action_toggle_selection(self) -> None:
            """Called when the user presses space. Toggles the selection state."""
            tree = self.query_one(Tree)
            node = tree.cursor_node
            if not node:
                return

            new_state = not self._is_fully_selected(node)
            self._set_node_and_children_selected(node, new_state)
            self._update_all_labels()

        def _update_all_labels(self):
            """Recalculates labels for the entire tree and refreshes the view."""
            tree = self.query_one(Tree)
            self._recalculate_and_set_label(tree.root)
            tree.refresh()

        def _recalculate_and_set_label(self, node: TreeNode) -> str:
            """
            Recursively determines the visual status of a node and sets its label.
            """
            status = 'none'
            if not node.data["is_dir"]:
                status = 'full' if node.data["selected"] else 'none'
            else:
                if not node.children:
                    status = 'full' if node.data["selected"] else 'none'
                else:
                    child_statuses = {self._recalculate_and_set_label(child) for child in node.children}
                    if len(child_statuses) == 1:
                        status = child_statuses.pop()
                    else:
                        status = 'partial'

            if status == 'full':
                prefix = "[green]✓[/green]"
            elif status == 'partial':
                prefix = "[yellow]-[/yellow]"
            else:
                prefix = "[grey50]◦[/grey50]"

            icon = "📁" if node.data["is_dir"] else "📄"
            name = f"[b]{node.data['path'].name}[/b]" if node.data["is_dir"] else node.data['path'].name
            node.set_label(Text.from_markup(f"{prefix} {icon} {name}"))
            return status

        def action_confirm_selection(self) -> None:
            """Called on Enter. Collects all selected files and exits."""
            selected_files = []
            def collect(node: TreeNode):
                if not node.data["is_dir"] and node.data["selected"]:
                    selected_files.append(node.data["path"])
                for child in node.children:
                    collect(child)

            collect(self.query_one(Tree).root)
            self.exit(selected_files)


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


def run_config_command(args: argparse.Namespace, console: Console):
    """Handle the 'config' command logic based on parsed arguments."""
    if args.show:
        show_current_config(console)
    elif args.reset:
        if reset_config():
            console.print("[green]✓ Configuration has been reset to defaults.[/green]")
        else:
            console.print("[yellow]No configuration file found. Already using defaults.[/yellow]")
    else:
        # If no flags are provided, run the interactive wizard.
        if not HAS_QUESTIONARY:
             console.print("[red]Error:[/red] The 'questionary' package is required for the config wizard.")
             console.print("Please install it: [bold]pip install 'codetoprompt[interactive]'[/bold] or [bold]pip install questionary[/bold]")
             return 1
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
    table.add_row("Code Compression", str(config['compress']))
    table.add_row("Count Tokens", str(config['count_tokens']))
    table.add_row("Tree Depth", str(config['tree_depth']))
    table.add_row("Output Format", config.get('output_format', 'default'))
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
    new_config["compress"] = Confirm.ask(
        "Enable code compression by default (requires tree-sitter)?", default=current_config.get("compress")
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
    
    current_format = current_config.get("output_format", "default")
    new_config["output_format"] = Prompt.ask(
        "Default output format?",
        choices=["default", "markdown", "cxml"],
        default=current_format
    )

    save_config(new_config)
    console.print(f"\n[green]✓ Configuration saved to:[/] {get_config_path()}")


def run_prompt_generation(args: argparse.Namespace, console: Console):
    """The main logic for generating a prompt."""
    if not args.directory:
        console.print("[red]Error:[/red] A path to a directory is required for prompt generation.")
        create_main_parser().print_help()
        return 1

    try:
        directory = validate_directory(args.directory)

        config = load_config()
        include_patterns = [p.strip() for p in args.include.split(',')] if args.include else config["include_patterns"]
        exclude_patterns = [p.strip() for p in args.exclude.split(',')] if args.exclude else config["exclude_patterns"]
        explicit_files = None

        if args.interactive:
            if not HAS_TEXTUAL:
                console.print("[red]Error:[/red] The 'textual' package is required for interactive mode.")
                console.print("Please install it: [bold]pip install 'codetoprompt[interactive]'[/bold] or [bold]pip install textual[/bold]")
                return 1

            scanner = CodeToPrompt(
                root_dir=str(directory),
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                respect_gitignore=args.respect_gitignore,
            )
            candidate_files = scanner._get_files_to_process()

            if not candidate_files:
                console.print("[yellow]No files found to select from based on current filters.[/yellow]")
                return 0
            
            app = FileSelectorApp(root_path=directory, candidate_files=set(candidate_files))
            selected_files = app.run()

            if selected_files is None:
                console.print("\n[yellow]Interactive selection cancelled.[/yellow]")
                return 0
            
            explicit_files = selected_files

        display_config = {
            "Root Directory": str(directory), "Include Patterns": include_patterns or ['*'], "Exclude Patterns": exclude_patterns or [],
            "Respect .gitignore": args.respect_gitignore, "Show Line Numbers": args.show_line_numbers,
            "Count Tokens": args.count_tokens, "Compress Code": args.compress, "Max Tokens": args.max_tokens or "Unlimited", "Tree Depth": args.tree_depth,
            "Output Format": args.output_format, "Interactive Mode": args.interactive,
        }
        show_config_panel(console, display_config, "CodeToPrompt")

        processor = CodeToPrompt(
            root_dir=str(directory), include_patterns=include_patterns, exclude_patterns=exclude_patterns, compress=args.compress,
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


def show_config_panel(console: Console, config: dict, title: str):
    """Show configuration panel for a run."""
    config_text = "[bold]Configuration for this run:[/bold]\n"
    for key, value in config.items():
        config_text += f"{key}: {value}\n"
    panel = Panel.fit(config_text.strip(), title=title, border_style="blue")
    console.print(panel)


def show_summary_panel(console: Console, processor: CodeToPrompt, count_tokens_enabled: bool, output_file: str, clipboard_success: bool):
    """Show summary panel for prompt generation."""
    destination = "Clipboard" if not output_file else output_file
    if not output_file and not clipboard_success:
        destination = "stdout (clipboard copy failed)"
    
    token_count_str = f"{processor.get_token_count():,}" if count_tokens_enabled else 'Not counted'

    summary_text = (
        f"[bold]Summary:[/bold]\n"
        f"Files Processed: {len(processor.processed_files)}\n"
        f"Total Tokens: {token_count_str}\n"
        f"Output Destination: {destination}"
    )
    if not output_file:
         summary_text += f"\nCopied to Clipboard: {'Yes' if clipboard_success else 'No'}"

    if count_tokens_enabled and processor.processed_files:
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