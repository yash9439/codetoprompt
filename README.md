# CodeToPrompt

[![PyPI version](https://badge.fury.io/py/codetoprompt.svg)](https://badge.fury.io/py/codetoprompt)
[![PyPI Downloads](https://static.pepy.tech/badge/codetoprompt)](https://pepy.tech/projects/codetoprompt)

**CodeToPrompt** is a powerful command-line and Python tool that transforms your entire codebase into a single, context-rich prompt optimized for Large Language Models (LLMs). It supports compression, intelligent file filtering, multiple output formats (including Claude XML and Markdown), and in-depth analysis of your project.

---

## 🔧 Installation

Install from PyPI:

```bash
pip install codetoprompt
```

For clipboard functionality on Linux, you may need to install a system dependency:
```bash
# Debian/Ubuntu
sudo apt-get install xclip

# Fedora
sudo dnf install xclip

# Arch Linux
sudo pacman -S xclip
```
(The tool also supports `wl-clipboard` on Wayland automatically.)

---

## 🚀 Basic Usage

The two core commands are `codetoprompt` (or `ctp`) for generating prompts and `analyse` for inspecting your project.

### Generate a Prompt from a Codebase

This is the main command. It scans your project and copies a context-rich prompt to your clipboard.

```bash
codetoprompt <path>
```

**Example Run:**

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

### Run Codebase Analysis

Before generating a prompt, get a high-level overview of your project's composition and token count.

```bash
codetoprompt analyse <path>
```
**Example Analysis:**
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

---

## 🧠 Advanced Features

### 📄 Output Formats

Tailor the output for different LLMs or use cases.

#### Default Format (`codetoprompt <path>`)
Clean and simple, with a project tree and file contents.
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

#### Markdown Format (`--markdown` or `-m`)
Formats the output as a single Markdown document with language-specific code blocks.
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

#### Claude XML Format (`--cxml` or `-c`)
Wraps each file in XML tags, a format that Claude models handle well.
```xml
<documents>
  <document index="1">
    <source>main.py</source>
    <document_content>
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
    </document_content>
  </document>
</documents>
```

### 🧬 Smart Code Compression

For large codebases, the `--compress` flag is essential. It analyzes supported code files and generates a high-level summary instead of including the full code.

```bash
codetoprompt <path> --compress
```

**Supported Languages for Compression:** This feature currently analyzes and summarizes `Python`, `JavaScript`, `TypeScript`, `Java`, `C`, `C++`, and `Rust` files. Other files will be included in full.

**Example Compressed Output for a Python File:**
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
> **Automatic Data File Handling:** To further manage token count, `codetoprompt` automatically detects common data files (like `.csv`, `.json`, and `.jsonl`) and includes **only the first 5 lines**. This provides a sample of the data's structure without overwhelming the prompt. This behavior is automatic and does not require a special flag.

### 🎛️ Command-Line Options

Here is the full list of options for the main `codetoprompt` command.

| Option | Alias | Description |
| :--- | :---: | :--- |
| `--output <file>` | | Save the prompt to a file. **This overrides the default clipboard behavior.** |
| `--include <patterns>` | | Comma-separated glob patterns for files to include (e.g., `"*.py,*.js"`). |
| `--exclude <patterns>` | | Comma-separated glob patterns for files to exclude (e.g., `"*.pyc,dist/*"`). |
| `--markdown` | `-m` | Format output as a single Markdown document. |
| `--cxml` | `-c` | Format output using Claude-friendly XML tags. |
| `--compress` | | Use smart code compression to summarize files and reduce tokens. |
| `--show-line-numbers` | | Prepend line numbers to code. Use `--no-show-line-numbers` to disable. |
| `--respect-gitignore` | | Respect `.gitignore` rules (default). Use `--no-respect-gitignore` to disable. |
| `--max-tokens <num>` | | Warn if token count exceeds this limit. Does not truncate. |
| `--tree-depth <num>` | | Set the maximum depth for the project structure tree. |
| `--version` | `-v` | Display the installed version number. |
| `--help` | `-h` | Show this help message and exit. |


---

## ⚙️ Configuration

Set your preferred defaults using the `config` command. Settings are saved in `~/.config/codetoprompt/config.toml`.

#### Show Current Config (`codetoprompt config --show`)
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

#### Interactive Configuration Wizard (`codetoprompt config`)
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

#### Reset to Defaults (`codetoprompt config --reset`)
```
╭───────────────── Configuration Reset ────────────────╮
│ Configuration has been reset to default values.       │
╰──────────────────────────────────────────────────────╯
```

---

## 🐍 Python API

Use `codetoprompt` programmatically in your own Python scripts for maximum flexibility.

```python
from codetoprompt import CodeToPrompt

ctp = CodeToPrompt(
    root_dir="path/to/project",
    include_patterns=["*.py"],
    exclude_patterns=["tests/*"],
    compress=True,
)

# Generate a prompt string
prompt = ctp.generate_prompt()

# Get a detailed analysis dictionary
analysis = ctp.analyse()
```

---

## 🤝 Contributing

We welcome contributions! Please open a PR or issue to get started.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for full details.