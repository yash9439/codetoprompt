# CodeToPrompt

[![CI](https://github.com/yash9439/codetoprompt/actions/workflows/ci.yml/badge.svg)](https://github.com/yash9439/codetoprompt/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/codetoprompt.svg)](https://badge.fury.io/py/codetoprompt)
[![PyPI Downloads](https://static.pepy.tech/badge/codetoprompt)](https://pepy.tech/projects/codetoprompt)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/codetoprompt)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**`codetoprompt` is a powerful command-line tool that transforms local codebases, GitHub repositories, web pages, and online documents into a single, context-rich prompt optimized for Large Language Models (LLMs).**

It streamlines the process of providing comprehensive context to LLMs by intelligently selecting, compressing, and formatting project files and remote content.

---

<!-- 
TODO: Add a GIF demonstrating the key features:
1. Running `ctp .` on a local directory.
2. Running `ctp <github_url>`.
3. Launching the interactive mode with `ctp . -i` and selecting files.
-->

## ✨ Key Features

*   **Universal Context Sources**: Ingests code from **local directories**, **GitHub repos**, **web pages**, **YouTube transcripts**, **ArXiv papers**, and **PDFs**.
*   **Intelligent Code Compression**: Uses `tree-sitter` to parse code into a structural summary, drastically reducing token count while preserving the high-level architecture.
*   **Interactive TUI Mode**: Launch a fast, lazy-loaded terminal UI to visually select the exact files and directories you need.
*   **Flexible Output Formats**: Generate prompts in a simple default format, as a single **Markdown** file, or in **Claude-friendly XML**.
*   **Automatic File Handling**: Natively processes **Jupyter Notebooks**, samples large data files (like `.csv` or `.json`), and respects your `.gitignore` rules.
*   **Powerful Filtering**: Fine-tune your context with `--include` and `--exclude` glob patterns.
*   **In-Depth Analysis**: Run the `analyse` command to get a full breakdown of your project's languages, token counts, and file sizes before generating a prompt.
*   **Snapshots and Diffs**: Save a JSON snapshot of a project and generate a unified diff against it. Diff is copied to clipboard by default (summary only shown in terminal), or written to a file with `--output`.

## 🔧 Installation

Install from PyPI:

```bash
pip install codetoprompt
```

For clipboard functionality on Linux, you may need to install `xclip` or `wl-clipboard`:
```bash
# Debian/Ubuntu
sudo apt-get install xclip

# Arch Linux
sudo pacman -S xclip
```

---

## 🚀 Quick Start

The two core commands are `codetoprompt` (or `ctp`) for generating prompts and `analyse` for inspecting your project.

#### 1. Generate a Prompt from a Local Codebase

Scan your current project, respect `.gitignore`, and copy a context-rich prompt to your clipboard.

```bash
# Long version
codetoprompt .

# Short version
ctp .
```

#### 2. Generate a Prompt from any URL

Pass a supported URL to fetch and process remote content automatically.

```bash
# From a GitHub Repository
ctp https://github.com/yash9439/codetoprompt

# From a documentation page
ctp https://python-poetry.org/docs/

# From a YouTube video transcript
ctp https://www.youtube.com/watch?v=cAkMcPfY_Ns
```

#### 3. Create a Snapshot (local only)

```bash
# Save a JSON snapshot of the current project
codetoprompt snapshot . --output snap.json
```

#### 4. Diff Against a Snapshot (local only)

```bash
# Copies the full diff to the clipboard; terminal shows only a summary
codetoprompt diff . --snapshot snap.json

# Save the full diff to a file instead of copying to clipboard
codetoprompt diff . --snapshot snap.json --output diff.txt
```

---

## 🧠 Features in Detail

### 1. Universal Context Gathering

`codetoprompt` can pull in context from almost anywhere.

| Source Type | Example Command | Description |
| :--- | :--- | :--- |
| **Local Directory** | `ctp path/to/your/project` | Scans a local codebase, respecting `.gitignore` and applying filters. |
| **GitHub Repo** | `ctp https://github.com/user/repo` | Fetches all text-based files and builds a complete project prompt. |
| **Web Page** | `ctp https://en.wikipedia.org/wiki/API` | Strips boilerplate and extracts the core text content. |
| **YouTube Video** | `ctp <youtube_url>` | Automatically extracts the full video transcript. |
| **ArXiv Paper** | `ctp https://arxiv.org/abs/2203.02155` | Downloads the full PDF from an abstract page and extracts its text. |
| **PDF Document** | `ctp <url_to_pdf>` | Directly downloads and extracts text from any public PDF link. |
| **Jupyter Notebook** | `(automatic)` | `.ipynb` files in a local project are automatically converted to Python code. |

### 2. Interactive File Selection (`--interactive` or `-i`)

For ultimate control, the `--interactive` flag launches a Terminal User Interface (TUI) allowing you to manually select which files and directories to include. It's perfect for cherry-picking specific features or excluding noisy test files.

```bash
ctp . --interactive
```

> **Optimized for Large Projects:** The interactive file tree uses **lazy loading**, meaning it only loads a directory's contents when you expand it. This keeps the interface fast and responsive, even in massive codebases.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     |
│                        FileSelectorApp                              |
│           Navigate: ↑/↓/w/s  | Expand/Collapse: ←/a/d               |
|               Toggle Select: Space | Confirm: Enter                 |
│       ✓ = All selected | - = Some selected | ◦ = None selected      |
│ ────────────────────────────────────────────────────────────────────│
│                                                                     |
│ ▶ 📁 .github                                                        |
│ ▼ - 📁 codetoprompt                                                 |
│ >   ▼ ✓ 📁 compressor                                               |
│         ✓ 📁 analysers                                              |
│         ✓ 📁 formatters                                             |
│         ✓ 📄 __init__.py                                            |
│         ✓ 📄 compressor.py                                          |
│     ◦ 📄 __init__.py                                                |
│     ◦ 📄 analysis.py                                                |
│     ◦ 📄 arg_parser.py                                              |
│     ◦ 📄 cli.py                                                     |
│     ◦ 📄 config.py                                                  |
│     ◦ 📄 core.py                                                    |
│     ◦ 📄 interactive.py                                             |
│     ◦ 📄 utils.py                                                   |
│     ◦ 📄 version.py                                                 |
│ ▶ 📁 codetoprompt.egg-info                                          |
│ ▶ 📁 tests                                                          |
│ ◦ 📄 .gitignore                                                     |
│ ◦ 📄 CHANGELOG.md                                                   |
│ ◦ 📄 CONTRIBUTING.md                                                |
│ ◦ 📄 LICENSE                                                        |
│ ◦ 📄 MANIFEST.in                                                    |
│ ◦ 📄 pyproject.toml                                                 |
│ ◦ 📄 pytest.ini                                                     |
│ ◦ 📄 README.md                                                      |
│                                                                     |
│ q Quit                                                              |
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Smart Code Compression (`--compress`)

For large codebases, the `--compress` flag is essential. It analyzes supported code files and generates a high-level summary instead of including the full code, drastically reducing the final token count.

```bash
ctp . --compress
```

**Supported Languages:** `Python`, `JavaScript`, `TypeScript`, `Java`, `C`, `C++`, and `Rust`. Other files (like `README.md`) are included in full.

**Example Compressed Output for a Python File:**
```
# File: codetoprompt/core.py
# Language: python

## Imports:
- import platform
- from pathlib import Path
- ...

## Classes:
### class CodeToPrompt:
    """Convert code files to prompt format."""
    def __init__(self, root_dir, ...): ...
    def generate_prompt(self, progress): ...
    def analyse(self, progress, top_n): ...
```
> **Smart Data File Handling:** `codetoprompt` treats `.csv`, `.json`, and `.jsonl` files specially to keep prompts useful without exploding token counts:
> - **Small datasets pass through in full.** A file is only truncated if it exceeds `data_file_threshold_lines` (default **50**), so a 12-row config or sample dataset is included verbatim.
> - **Large datasets are cut to the first 5 lines** with a truncation note appended.
> - **Repetitive per-record layouts are clustered.** When a single directory contains more than `data_file_max_per_dir` files of the same data extension (default **5**), only that many are kept and the rest are summarized in an `Omitted Data File Groups` section. This stops 50 near-identical JSON record files from drowning out the rest of your code.
> - **Toggle off entirely** with `--no-truncate-data-files` (or set `truncate_data_files = false` in config) to always include data files in full. Set `--data-file-max-per-dir 0` to disable clustering.

### 4. Adaptable Output Formats

Tailor the output for different LLMs or use cases using format flags.

| Format | Flag | Description |
| :--- | :--- | :--- |
| **Default** | (none) | Clean, human-readable format with file paths and fenced code blocks. |
| **Markdown**| `--markdown` or `-m` | A single Markdown document, great for viewing or sharing. |
| **Claude XML**| `--cxml` or `-c` | Wraps each file in `<document>` tags, a format Claude models handle exceptionally well. |

**Example CXML Output (`-c`):**
```xml
<documents>
  <document index="1">
    <source>main.py</source>
    <document_content>
def main():
    print("Hello, World!")
    </document_content>
  </document>
</documents>
```

### 5. In-Depth Project Analysis (`analyse`)

Before generating a prompt, get a high-level overview of your local project's composition and token count. This helps you decide which filters or compression strategies to apply.

```bash
ctp analyse .
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
╭─ Overall Project Summary ─╮
│ Total Files: 47           │
│ Total Lines: 6,033        │
│ Total Tokens: 49,834      │
╰───────────────────────────╯
             Analysis by File Type (Top 10)             
┏━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Extension ┃ Files ┃ Tokens ┃ Lines ┃ Avg Tokens/File ┃
┡━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ .py       │    32 │ 37,901 │ 4,650 │           1,184 │
│ .md       │     3 │  5,069 │   544 │           1,690 │
│ .<no_ext> │     3 │  4,807 │   559 │           1,602 │
│ .toml     │     1 │    827 │   117 │             827 │
│ .txt      │     4 │    582 │    68 │             146 │
│ .yml      │     1 │    361 │    56 │             361 │
│ .yaml     │     1 │    229 │    30 │             229 │
│ .ini      │     1 │     45 │     6 │              45 │
│ .in       │     1 │     13 │     3 │              13 │
└───────────┴───────┴────────┴───────┴─────────────────┘
               Largest Files by Tokens (Top 10)               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┓
┃ File Path                                 ┃ Tokens ┃ Lines ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━┩
│ codetoprompt/core.py                      │  5,037 │   538 │
│ codetoprompt.egg-info/PKG-INFO            │  4,453 │   493 │
│ README.md                                 │  2,910 │   285 │
│ codetoprompt/compressor/analysers/cpp.py  │  2,276 │   272 │
│ codetoprompt/compressor/analysers/rust.py │  2,214 │   271 │
│ codetoprompt/interactive.py               │  2,125 │   270 │
│ codetoprompt/compressor/analysers/java.py │  2,090 │   245 │
│ codetoprompt/cli.py                       │  1,877 │   207 │
│ tests/test_core.py                        │  1,743 │   179 │
│ CHANGELOG.md                              │  1,701 │   183 │
```

---

## 🎛️ Command-Line Reference

Here is the full list of options for the main `codetoprompt` command.

| Option | Alias | Description | Scope |
| :--- | :---: | :--- | :---: |
| `--output <file>` | | Save the prompt to a file instead of the clipboard. | All |
| `--markdown` | `-m` | Format output as a single Markdown document. | All |
| `--cxml` | `-c` | Format output using Claude-friendly XML tags. | All |
| `--max-tokens <num>`| | Warn if token count exceeds this limit. Does not truncate. | All |
| `--include <pats>` | | Comma-separated glob patterns for files to include (e.g., "*.py,*.js"). | Local |
| `--exclude <pats>` | | Comma-separated glob patterns for files to exclude (e.g., "*.pyc,dist/*"). | Local |
| `--interactive` | `-i` | Launch an interactive TUI to select files. | Local |
| `--compress` | | Use smart code compression to summarize files. | Local |
| `--show-line-numbers` | | Prepend line numbers to code. | Local |
| `--file-max-lines <num>` | | Truncate any file exceeding this many lines. | Local |
| `--file-max-bytes <num>` | | Truncate any file exceeding this many bytes. | Local |
| `--no-truncate-data-files` | | Always include data files (`.csv`/`.json`/`.jsonl`) in full. | Local |
| `--data-file-threshold-lines <num>` | | Only truncate data files larger than this. Default: 50. | Local |
| `--data-file-max-per-dir <num>` | | Cap on same-extension data files kept per directory; 0 disables. Default: 5. | Local |
| `--respect-gitignore` | | Respect `.gitignore` rules (default). Use `--no-respect-gitignore` to disable. | Local |
| `--tree-depth <num>` | | Set the maximum depth for the project structure tree. | Local |
| `--version` | `-v` | Display the installed version number. | N/A |
| `--help` | `-h` | Show the help message and exit. | N/A |

### Subcommands

- **Analyse**: `codetoprompt analyse <PATH> [--include ...] [--exclude ...]`
- **Snapshot**: `codetoprompt snapshot <PATH> --output <snapshot.json> [--include ...] [--exclude ...] [--respect-gitignore|--no-respect-gitignore]`
- **Diff**: `codetoprompt diff <PATH> --snapshot <snapshot.json> [--use-snapshot-filters] [--include ...] [--exclude ...] [--output <file>]`

---

## ⚙️ Configuration

Set your preferred defaults once using the `config` command. Settings are saved in `~/.config/codetoprompt/config.toml`.

*   **Interactive Wizard**: `ctp config`
*   **Show Current Config**: `ctp config --show`
*   **Reset to Defaults**: `ctp config --reset`

Additional data-file settings (configurable via the wizard or directly in `config.toml`):

- **Truncate Data Files**: `truncate_data_files` (default: `true`). Master toggle.
- **Data File Threshold Lines**: `data_file_threshold_lines` (default: `50`). Files at or below this size are kept in full even when truncation is on.
- **Data File Max Per Dir**: `data_file_max_per_dir` (default: `5`). When a directory contains more same-extension data files than this, only the first N (sorted) are processed and the rest are summarized in the prompt. Set to `0` to disable.

Additional snapshot-related settings:

- **Snapshot Max Bytes**: `snapshot_max_bytes` (default: 3 MB). If a text file exceeds this size, its content is not inlined into the snapshot.
- **Snapshot Max Lines**: `snapshot_max_lines` (default: 20,000). If a text file exceeds this line count, its content is not inlined into the snapshot.

> Snapshot always requires `--output`. Diff copies to clipboard by default (summary only printed to terminal). Provide `--output <file>` to write the diff to a file instead of copying.

---

## 🐍 Python API

Use `codetoprompt` programmatically in your own Python scripts for maximum flexibility.

```python
from codetoprompt import CodeToPrompt
# conceptual imports for a full use-case
# from some_llm_library import LlmClient 

# 1. Process a local directory with compression and XML format
ctp_local = CodeToPrompt(
    target="path/to/your/project",
    compress=True,
    output_format="cxml",
    exclude_patterns=["tests/*", "docs/*"]
)
prompt = ctp_local.generate_prompt()
analysis = ctp_local.analyse()

print(f"Project Analysis: {analysis['overall']}")
print(f"Generated a prompt with {ctp_local.get_token_count()} tokens.")

# 2. Conceptually, you'd then use this with an LLM client
# client = LlmClient(api_key="...")
# response = client.completions.create(
#     model="claude-3-opus-20240229", # CXML is great for Claude
#     messages=[
#         {"role": "user", "content": f"Here is a codebase:\n{prompt}\nPlease explain the main purpose of the `core.py` file."},
#     ]
# )
# print(response)

# 3. Process a remote URL
ctp_remote = CodeToPrompt(target="https://github.com/yash9439/codetoprompt")
remote_prompt = ctp_remote.generate_prompt()
print(f"Generated a prompt from GitHub with {ctp_remote.get_token_count()} tokens.")
```

---

## 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for development setup and guidelines. Feel free to open a PR or issue to get started.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for full details.
