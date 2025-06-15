# CodeToPrompt

[![PyPI version](https://badge.fury.io/py/codetoprompt.svg)](https://badge.fury.io/py/codetoprompt)

Convert your entire codebase into a single, context-rich prompt for Large Language Models (LLMs), perfectly formatted for direct use.

## Features

- **Comprehensive Project Context**: Automatically includes Git repository information and a visual project structure tree.
- **Flexible Output Formats**: Generate prompts in different formats using CLI flags: `--markdown` for standard Markdown code blocks and `--cxml` for a Claude-friendly XML structure.
- **Intelligent Code Compression**: Use the `--compress` flag to dramatically reduce token count. It uses `tree-sitter` to parse code into a structural summary, preserving classes, functions, and signatures while omitting implementation details.
- **In-Depth Codebase Analysis**: Run `codetoprompt analyse` to get a detailed statistical report on your project's composition, including token counts by file type and largest files.
- **Persistent Configuration**: Run a one-time interactive setup (`codetoprompt config`) to set your personal defaults for all options.
- **Smart File Filtering**: Respects `.gitignore` rules by default and offers powerful include/exclude glob patterns to precisely select the files you need.
- **Token-Aware**: Counts tokens to help you stay within your LLM's context window and provides an informative summary with token-based insights.
- **Developer-Friendly**: Copies the final prompt directly to your clipboard for immediate use, with a rich and informative CLI.
- **Robust and Safe**: Safely reads files with fallback encodings and automatically skips binary files.
- **Dual Interface**: Use it as a simple command-line tool or import it as a Python library.

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

`codetoprompt` is designed to be intuitive and has three main commands: `codetoprompt <path>` for prompt generation, `codetoprompt analyse <path>` for analysis, and `codetoprompt config` for settings.

### Generating a Prompt

This is the primary function. Simply point `codetoprompt` at a directory.

```shell
codetoprompt .
```

This will process the current directory, copy the result to your clipboard, and show you a detailed summary.

#### Formatting the Output

You can control the output format for better integration with different models or tools.

- **Markdown (`-m`, `--markdown`)**: Outputs each file's content in a standard, clean Markdown code block. This is great for general-purpose use.

  ```shell
  codetoprompt . -m
  ```

  *Sample Markdown Output Snippet:*
  ```markdown
  codetoprompt/cli.py
  ```python
  #!/usr/bin/env python3

  import argparse
  import sys
  # ... (rest of file content)
  ```
  ```

- **Claude XML (`-c`, `--cxml`)**: Wraps each file's content in `<document>` XML tags, a format optimized for Anthropic's Claude models.

  ```shell
  codetoprompt . -c
  ```

  *Sample CXML Output Snippet:*
  ```xml
  <documents>
    <document index="1">
      <source>codetoprompt/cli.py</source>
      <document_content>
      #!/usr/bin/env python3

      import argparse
      # ... (rest of file content)
      </document_content>
    </document>
    ...
  </documents>
  ```

#### Compressing Code to Save Tokens

When dealing with large codebases, the `--compress` flag is essential. It analyzes supported code files (Python, JS, TS, Java, C/C++, Rust) and generates a high-level summary instead of including the full code. This drastically reduces the token count while preserving the project's architecture.

```shell
codetoprompt . --compress
```

Files that cannot be compressed (like `README.md` or unsupported languages) are automatically included in their entirety.

*Sample Compressed Output for a Python File:*
```
# File: codetoprompt/core.py
# Language: python

## Imports:
- import platform
- import subprocess
- from pathlib import Path
- ...

## Classes:
### class CodeToPrompt:
    """Convert code files to prompt format."""
    def __init__(self, root_dir, ...):
        ...
    def _get_compressor(self):
        ...
    def _get_git_repo(self):
        ...
    def generate_prompt(self, progress):
        ...
    def analyze(self, progress, top_n):
        ...
    def copy_to_clipboard(self):
        ...
```

#### Sample Prompt Generation Output

```text
╭───────────────── CodeToPrompt ──────────────────╮
│ Configuration for this run:                     │
│ Root Directory: .                               │
│ Include Patterns: ['*.py', '*.md']              │
│ Exclude Patterns: ['tests/*']                   │
│ Respect .gitignore: True                        │
│ Show Line Numbers: False                        │
│ Count Tokens: True                              │
│ Max Tokens: 16,000                              │
│ Tree Depth: 3                                   │
╰─────────────────────────────────────────────────╯
✓ Processing files... ━━━━━━━━━━━━━━━━━━━━━━━━ 100%
╭──────────────── Processing Complete ───────────────╮
│ Summary:                                           │
│ Files Processed: 42                                │
│ Total Tokens: 11,258                               │
│ Output Destination: Clipboard                      │
│ Copied to Clipboard: Yes                           │
│                                                    │
│ Top 3 Files by Tokens:                             │
│   - codetoprompt/core.py (2,845 tokens)            │
│   - codetoprompt/cli.py (2,101 tokens)             │
│   - README.md (988 tokens)                         │
│                                                    │
│ Top 5 Extensions by Tokens:                        │
│   - .py (8,432 tokens)                             │
│   - .md (2,130 tokens)                             │
│   - .yml (451 tokens)                              │
│   - .toml (180 tokens)                             │
│   - .gitignore (65 tokens)                         │
╰────────────────────────────────────────────────────╯
```

### Analyzing a Codebase

To get insights into your project's structure without generating a prompt, use the `analyse` command.

```shell
codetoprompt analyse .
```

This provides a clean, statistical report on file counts, lines of code, and token distribution.

#### Sample Analysis Output

```text
╭────────────────── Codebase Analysis ─────────────────╮
│ Configuration for this run:                          │
│ Root Directory: .                                    │
│ Include Patterns: ['*']                              │
│ Exclude Patterns: []                                 │
│ Respect .gitignore: True                             │
╰──────────────────────────────────────────────────────╯
✓ Processing files... ━━━━━━━━━━━━━━━━━━━━━━━━ 100%
╭── Overall Project Summary ───╮
│ Total Files:  42             │
│ Total Lines:  1,890          │
│ Total Tokens: 11,258         │
╰──────────────────────────────╯
╭─────────── Analysis by File Type (Top 10) ──────────────╮
│ Extension   │ Files │ Tokens │  Lines │ Avg Tokens/File │
├─────────────┼───────┼────────┼────────┼─────────────────┤
│ .py         │    12 │  8,432 │  1,200 │             702 │
│ .md         │     3 │  2,130 │    450 │             710 │
│ .yml        │     1 │    451 │     80 │             451 │
│ .toml       │     2 │    180 │     60 │              90 │
│ .gitignore  │     1 │     65 │     30 │              65 │
──────────────────────────────────────────────────────────╯
╭─── Largest Files by Tokens (Top 10) ────╮
│ File Path              │ Tokens │ Lines │
├────────────────────────┼────────┼───────┤
│ codetoprompt/core.py   │  2,845 │   400 │
│ codetoprompt/cli.py    │  2,101 │   350 │
│ README.md              │    988 │   200 │
│ CHANGELOG.md           │    850 │   180 │
│ pyproject.toml         │    110 │    40 │
╰─────────────────────────────────────────╯
```

### Configuration Management

`codetoprompt` remembers your preferences so you don't have to type them every time. The `config` command is your entrypoint for all settings management.

#### Interactive Setup (`codetoprompt config`)

Run the interactive wizard to set your personal defaults, including your preferred output format and whether to enable compression by default. This is a one-time setup.

```shell
codetoprompt config
```

#### Viewing Your Defaults (`codetoprompt config --show`)

To see what your current saved settings are, use the `--show` flag.

```shell
codetoprompt config --show
```

#### Resetting Your Defaults (`codetoprompt config --reset`)

If you want to clear your custom settings and return to the original defaults, use the `--reset` flag.

```shell
codetoprompt config --reset
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
    tree_depth=3,
    output_format="markdown",  # Or "cxml", "default"
    compress=True              # Enable code compression
)

# 1. Generate the complete prompt string
prompt = processor.generate_prompt()
print("Generated prompt!")

# 2. Save the prompt to a file
processor.save_to_file("prompt.txt")
print("Saved prompt to prompt.txt")

# 3. Get statistics about the generated prompt
stats = processor.get_stats()
print(f"\n--- Stats ---")
print(f"Total files processed: {stats['files_processed']}")
print(f"Total lines: {stats['total_lines']}")
print(f"Total tokens: {stats['total_tokens']}")
```

## License

MIT License - see LICENSE file for details