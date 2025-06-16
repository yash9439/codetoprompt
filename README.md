# CodeToPrompt

[![PyPI version](https://badge.fury.io/py/codetoprompt.svg)](https://badge.fury.io/py/codetoprompt)
[![PyPI Downloads](https://static.pepy.tech/badge/codetoprompt)](https://pepy.tech/projects/codetoprompt)

Convert your entire codebase into a single, context-rich prompt for Large Language Models (LLMs), perfectly formatted for direct use. It supports multiple output formats, code analysis, and intelligent file filtering.

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
(Supports wl-clipboard on Wayland as well)

## Basic Usage

### Generate a Prompt

```bash
codetoprompt <path>
```

This will generate a prompt from all files in the specified directory, respecting `.gitignore` rules by default.

Example output:
```
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

### Analyse Codebase

```bash
codetoprompt analyse <path>
```

This will provide a detailed analysis of your codebase, including:
- Overall statistics (files, tokens, lines)
- Statistics by file extension
- Top files by token count

Example output:
```
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
╰─────────────────────────────────────────────────────────╯
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

## Advanced Features

### Output Formats

1. **Default Format** (default)
   ```bash
   codetoprompt <path>
   ```
   Output includes:
   - Project structure
   - File contents with relative paths

   Example output:
   ```
   Project Structure:
   .
   ├── src/
   │   ├── main.py
   │   └── utils.py
   └── tests/
       └── test_main.py

   Relative File Path: src/main.py
   ```python
   def main():
       print("Hello, World!")

   if __name__ == "__main__":
       main()
   ```

2. **Markdown Format** (-m, --markdown)
   ```bash
   codetoprompt <path> -m
   # or
   codetoprompt <path> --markdown
   ```
   Output is formatted as a markdown document with:
   - Code blocks with language-specific syntax highlighting
   - Project structure as markdown lists

   Example output:
   ```markdown
   Project Structure:
   .
   ├── src/
   │   ├── main.py
   │   └── utils.py
   └── tests/
       └── test_main.py

   ## src/main.py
   ```python
   def main():
       print("Hello, World!")

   if __name__ == "__main__":
       main()
   ```

3. **Claude XML Format** (-c, --cxml)
   ```bash
   codetoprompt <path> -c
   # or
   codetoprompt <path> --cxml
   ```
   Output is formatted as XML for Claude:
   ```xml
   <documents>
     <document index="1">
       <source>main.py</source>
       <document_content>
         // Code content here
       </document_content>
     </document>
   </documents>
   ```

### File Filtering

1. **Include Specific Files**
   ```bash
   codetoprompt <path> --include "*.py" --include "src/**/*.js"
   ```

2. **Exclude Files**
   ```bash
   codetoprompt <path> --exclude "*.pyc" --exclude "node_modules/**"
   ```

3. **Gitignore Control**
   ```bash
   # Respect .gitignore (default)
   codetoprompt <path> --respect-gitignore
   
   # Ignore .gitignore rules
   codetoprompt <path> --no-respect-gitignore
   ```

### Code Compression

When dealing with large codebases, the `--compress` flag is essential. It analyses supported code files (Python, JS, TS, Java, C/C++, Rust) and generates a high-level summary instead of including the full code. This drastically reduces the token count while preserving the project's architecture.

The compression extracts:
- Import statements
- Function signatures with docstrings
- Class definitions with methods
- Key constants and type definitions

```bash
codetoprompt <path> --compress
```

Example output for a Python file with compression:
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
    def analyse(self, progress, top_n):
        ...
    def copy_to_clipboard(self):
        ...
```

> **Note on Large Data Files**: To further manage token count, `codetoprompt` automatically detects common data files (like `.csv`, `.json`) and includes only the first 5 lines. This provides a sample of the data's structure without overwhelming the prompt. This behavior is automatic and does not require a flag.

### Output Options

1. **Save to File**
   ```bash
   codetoprompt <path> --output output.txt
   ```

2. **Copy to Clipboard**
   ```bash
   codetoprompt <path> --clipboard
   ```

3. **Show Line Numbers**
   ```bash
   codetoprompt <path> --show-line-numbers
   ```

### Token and Tree Settings

1. **Set Maximum Tokens**
   ```bash
   codetoprompt <path> --max-tokens 1000
   ```
   Note: This only provides a warning if the output exceeds the specified token count. It does not truncate or limit the output.

2. **Tree Depth Control**
   ```bash
   codetoprompt <path> --tree-depth 3
   ```
   Note: This only affects the initial project structure tree display in the prompt. It does not limit the files processed.

### Other CLI Options

#### Version Check
To display the current version number, use the `--version` or `-v` flag:

```bash
codetoprompt --version
# or
ctp -v
```

#### Command Alias
For convenience, `codetoprompt` can be invoked using the shorter alias `ctp`. The following commands are equivalent:
```bash
codetoprompt . --analyse
ctp . --analyse
```

### Configuration

The `config` command helps manage your settings:

1. **Show Current Config**
   ```bash
   codetoprompt config --show
   ```
   Example output:
   ```
   ╭───────────────── Current Configuration ────────────────╮
   │ show_line_numbers = false                              │
   │ compress = false                                       │
   │ respect_gitignore = true                               │
   │ count_tokens = true                                    │
   │ max_tokens = null                                      │
   │ include_patterns = []                                  │
   │ exclude_patterns = []                                  │
   │ tree_depth = 5                                         │
   │ output_format = "default"                              │
   ╰───────────────────────────────────────────────────────╯
   ```

2. **Reset to Defaults**
   ```bash
   codetoprompt config --reset
   ```
   Example output:
   ```
   ╭───────────────── Configuration Reset ────────────────╮
   │ Configuration has been reset to default values.       │
   ╰──────────────────────────────────────────────────────╯
   ```

3. **Interactive Configuration**
   ```bash
   codetoprompt config
   ```
   Example output:
   ```
   ╭───────────────── Configuration Wizard ────────────────╮
   │ Would you like to show line numbers by default? [y/N] │
   │ Would you like to compress code by default? [y/N]     │
   │ Would you like to respect .gitignore by default? [Y/n]│
   │ Would you like to count tokens by default? [Y/n]      │
   │ Set maximum tokens (press Enter for no limit):        │
   │ Set default tree depth [5]:                           │
   │ Choose default output format:                         │
   │   1) default                                          │
   │   2) markdown                                         │
   │   3) cxml                                             │
   │ Choice [1]:                                           │
   ╰───────────────────────────────────────────────────────╯
   ```

## Configuration File

Settings are stored in `~/.config/codetoprompt/config.toml`:

```toml
[settings]
show_line_numbers = false
compress = false
respect_gitignore = true
count_tokens = true
max_tokens = null
include_patterns = []
exclude_patterns = []
tree_depth = 5
output_format = "default"
```

## Python API

You can also use codetoprompt as a library in your Python projects for more programmatic control:

```python
from codetoprompt import CodeToPrompt

# Initialize with options
ctp = CodeToPrompt(
    root_dir="path/to/project",
    include_patterns=["*.py"],
    exclude_patterns=["tests/*"],
    respect_gitignore=True,
    show_line_numbers=False,
    compress=False,
    max_tokens=None,
    tree_depth=5,
    output_format="default"
)

# Generate prompt
prompt = ctp.generate_prompt()

# Analyse codebase
analysis = ctp.analyse()

# Get file contents
files = ctp.get_files()
```

## Examples

1. **Basic Usage with Analysis**
   ```bash
   codetoprompt /path/to/project --analyse
   ```

2. **Generate Markdown Documentation**
   ```bash
   codetoprompt /path/to/project -m --output docs.md
   ```

3. **Create Claude-Compatible XML**
   ```bash
   codetoprompt /path/to/project -c --compress
   ```

4. **analyse Python Files Only**
   ```bash
   codetoprompt /path/to/project --include "*.py" --analyse
   ```

5. **Generate Prompt with Line Numbers**
   ```bash
   codetoprompt /path/to/project --show-line-numbers --output prompt.txt
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
