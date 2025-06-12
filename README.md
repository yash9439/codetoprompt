# CodeToPrompt

[![PyPI version](https://badge.fury.io/py/codetoprompt.svg)](https://badge.fury.io/py/codetoprompt)

Convert your entire codebase into a single, context-rich prompt for Large Language Models (LLMs), perfectly formatted for direct use.

## Features

- **Comprehensive Project Context**: Automatically includes Git repository information (current branch, latest commit) and a visual project structure tree.
- **Persistent Configuration**: Run a one-time interactive setup (`codetoprompt config`) to set your personal defaults for all options. No more repeating flags!
- **Smart File Filtering**: Respects `.gitignore` rules by default and offers powerful include/exclude glob patterns to precisely select the files you need.
- **Token-Aware**: Counts tokens to help you stay within your LLM's context window and warns you if you exceed your configured maximum.
- **Developer-Friendly**: Copies the final prompt directly to your clipboard for immediate use, with a rich and informative CLI.
- **Robust and Safe**: Safely reads files with fallback encodings and automatically skips binary files.
- **Dual Interface**: Use it as a simple command-line tool or import it as a Python library into your own projects.

## Installation

```bash
pip install codetoprompt
```

For clipboard support on Linux, you may need to install a system dependency:
```bash
# For Debian/Ubuntu
sudo apt-get install xclip

# For Fedora
sudo dnf install xclip

# For Arch Linux
sudo pacman -S xclip
```
*(Supports `wl-clipboard` on Wayland as well)*

## Usage

`codetoprompt` is designed to be intuitive. The main command takes a single argument: the path to the directory you want to process.

### Generating a Prompt

This is the primary function. Simply point `codetoprompt` at a directory.

```shell
codetoprompt .
```

This will process the current directory using your saved default settings, copy the result to your clipboard, and show you a summary.

#### Sample Output

```text
╭───────────────── CodeToPrompt ──────────────────╮
│ Configuration for this run:                     │
│ Root Directory: .                               │
│ Include Patterns: ['*.py', '*.md']              │
│ Exclude Patterns: ['tests/*']                   │
│ Respect .gitignore: True                        │
│ Show Line Numbers: False                        │
│ Count Tokens: True                              │
│ Max Tokens: 16000                               │
│ Tree Depth: 3                                   │
╰─────────────────────────────────────────────────╯
✓ Processing files... ━━━━━━━━━━━━━━━━━━━━━━━━ 100%
╭───────────── Processing Complete ─────────────╮
│ Summary:                                      │
│ Files Processed: 42                           │
│ Total Tokens: 11258                           │
│ Output Destination: Clipboard                 │
│ Copied to Clipboard: Yes                      │
╰───────────────────────────────────────────────╯
```

### Command-Line Help

For a full list of commands and arguments, use the `--help` flag.

```shell
codetoprompt --help
```

#### Sample Output

```text
usage: codetoprompt PATH [-h] [--output OUTPUT] [--include INCLUDE] [--exclude EXCLUDE] [--max-tokens MAX_TOKENS] [--tree-depth TREE_DEPTH]
                         [--respect-gitignore | --no-respect-gitignore] [--show-line-numbers | --no-show-line-numbers]
                         [--count-tokens | --no-count-tokens]

Converts a codebase into a single, context-rich prompt for LLMs.

positional arguments:
  PATH                  The path to the codebase directory to process (e.g., '.').

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Save the prompt to a file instead of copying to clipboard.
  --include INCLUDE     Comma-separated glob patterns of files to include.
  --exclude EXCLUDE     Comma-separated glob patterns of files to exclude.
  --max-tokens MAX_TOKENS
                        Warn if token count exceeds this limit.
  --tree-depth TREE_DEPTH
                        Maximum depth for the project structure tree.
  --respect-gitignore, --no-respect-gitignore
                        Respect .gitignore rules (overrides config).
  --show-line-numbers, --no-show-line-numbers
                        Prepend line numbers to code (overrides config).
  --count-tokens, --no-count-tokens
                        Count tokens in the prompt (improves speed, overrides config).

EXAMPLES:
  # Process the current directory
  codetoprompt .

  # Process a specific directory and save to a file
  codetoprompt /path/to/project --output my_prompt.txt

  # Process and exclude test files, respecting .gitignore
  codetoprompt . --exclude "tests/*,*.log" --respect-gitignore

CONFIGURATION:
  To set your default preferences (e.g., to always respect .gitignore),
  run the interactive wizard:
    codetoprompt config

  To view your current saved defaults:
    codetoprompt config --show

  To reset all settings to their original defaults:
    codetoprompt config --reset
```

### Configuration Management

`codetoprompt` remembers your preferences so you don't have to type them every time. The `config` command is your entrypoint for all settings management.

#### Interactive Setup (`codetoprompt config`)

Run the interactive wizard to set your personal defaults. This is a one-time setup.

```shell
codetoprompt config
```

##### Sample Session

```text
╭───────── CodeToPrompt Configuration Wizard ─────────╮
│ Set your preferred defaults. Press Enter to keep the│
│                  current value.                     │
╰─────────────────────────────────────────────────────╯
> Respect .gitignore files by default? [Y/n]: Y
> Show line numbers by default? [y/N]: N
> Count tokens by default (can be slow)? [Y/n]: Y
> Default directory tree depth? [3]: 5
> Default maximum token warning limit (0 or Enter for none)? [0]: 16000
> Default include patterns (comma-separated, Enter for all) []: *.py, *.md, Dockerfile
> Default exclude patterns (comma-separated) []: tests/*, .venv/*, node_modules/*

✓ Configuration saved to: /home/user/.config/codetoprompt/config.toml
```

#### Viewing Your Defaults (`codetoprompt config --show`)

To see what your current saved settings are, use the `--show` flag.

```shell
codetoprompt config --show
```

##### Sample Output

```text
╭─────────────── Current CodeToPrompt Defaults ───────────────╮
│ Setting              │ Value                                │
├──────────────────────┼──────────────────────────────────────┤
│ Respect .gitignore   │ True                                 │
│ Show Line Numbers    │ False                                │
│ Count Tokens         │ True                                 │
│ Tree Depth           │ 5                                    │
│ Max Tokens Warning   │ 16000                                │
│ Include Patterns     │ ['*.py', '*.md', 'Dockerfile']        │
│ Exclude Patterns     │ ['tests/*', '.venv/*', 'node_mod..'] │
╰─────────────────────────────────────────────────────────────╯
Config file location: /home/user/.config/codetoprompt/config.toml
```

#### Resetting Your Defaults (`codetoprompt config --reset`)

If you want to clear your custom settings and return to the original defaults, use the `--reset` flag.

```shell
codetoprompt config --reset
```

##### Sample Output
```text
✓ Configuration has been reset to defaults.
```

### Python API

You can also use `codetoprompt` as a library in your Python projects for more programmatic control.

```python
from codetoprompt import CodeToPrompt

# Initialize the processor with detailed options
processor = CodeToPrompt(
    root_dir="/path/to/your/codebase",
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["*.pyc", "__pycache__", "node_modules/*"],
    respect_gitignore=True,
    show_line_numbers=True,
    max_tokens=8000,
    tree_depth=3
)

# 1. Generate the complete prompt string
prompt = processor.generate_prompt()
print("Generated prompt!")

# 2. Save the prompt to a file
processor.save_to_file("prompt.txt")
print("Saved prompt to prompt.txt")

# 3. Copy the prompt to the clipboard
if processor.copy_to_clipboard():
    print("Copied to clipboard successfully.")
else:
    print("Could not copy to clipboard. Check dependencies.")

# 4. Get statistics about the generated prompt
stats = processor.get_stats()
print(f"\n--- Stats ---")
print(f"Total files processed: {stats['files_processed']}")
print(f"Total lines: {stats['total_lines']}")
print(f"Total tokens: {stats['total_tokens']}")
```

## License

MIT License - see LICENSE file for details