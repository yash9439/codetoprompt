"""Configuration management for CodeToPrompt."""

import toml
from pathlib import Path
from typing import Dict, Any, List, Optional

import argparse
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

APP_NAME = "codetoprompt"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Sensible defaults for a new user.
DEFAULT_CONFIG = {
    "show_line_numbers": False,
    "compress": False,
    "respect_gitignore": True,
    "count_tokens": True,
    "max_tokens": None,
    "include_patterns": [],
    "exclude_patterns": [],
    "tree_depth": 5,
    "output_format": "default",
}

def get_config_path() -> Path:
    """Returns the path to the config file."""
    return CONFIG_FILE

def load_config() -> Dict[str, Any]:
    """Loads configuration from the file, merging with defaults."""
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()
    if config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = toml.load(f)
            # A 'settings' table inside the toml file
            if "settings" in user_config and isinstance(user_config["settings"], dict):
                config.update(user_config["settings"])
        except Exception:
            # Fallback to defaults if config is invalid
            pass
    return config

def save_config(config: Dict[str, Any]):
    """Saves the configuration to the file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump({"settings": config}, f)

def reset_config() -> bool:
    """Deletes the configuration file, resetting to defaults.
    
    Returns True if the file existed and was deleted, False otherwise.
    """
    config_path = get_config_path()
    if config_path.is_file():
        config_path.unlink()
        return True
    return False

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

def show_config_panel(console: Console, config: dict, title: str):
    """Show configuration panel for a run."""
    config_text = "[bold]Configuration for this run:[/bold]\n"
    for key, value in config.items():
        config_text += f"{key}: {value}\n"
    panel = Panel.fit(config_text.strip(), title=title, border_style="blue")
    console.print(panel)