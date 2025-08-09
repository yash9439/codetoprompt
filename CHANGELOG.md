# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## \[0.7.1] - 2025-08-08
### Added

*   **Snapshot Command**: `codetoprompt snapshot <PATH> --output <snapshot.json>` to save a JSON snapshot of a local project (no git required).
    *   `--output` is required for this command.
*   **Diff Command**: `codetoprompt diff <PATH> --snapshot <snapshot.json>` to show a unified diff between the current project state and a previous snapshot.
    *   By default, the diff is copied to the clipboard when no `--output` is provided (if `pyperclip` is available; on Linux ensure `xclip` or `wl-copy`).
    *   Providing `--output <file>` writes the diff to the given path instead of copying to the clipboard.
*   **Configurable Snapshot Thresholds**: Set via `codetoprompt config`:
    *   `snapshot_max_bytes` (default 3 MB)
    *   `snapshot_max_lines` (default 20,000)

### Notes

*   Diff supports `--use-snapshot-filters` to reuse include/exclude and `.gitignore` behavior from the snapshot; you can override with flags.

---
## \[0.7.0] - 2025-07-31
### Improved

*   **Documentation**: Overhauled `README.md` for improved clarity, professionalism, and visual appeal.
    *   Replaced the introductory slogan with a more descriptive summary of the tool's purpose.
    *   Added a prominent "Key Features" section for a quick overview of capabilities.
    *   Updated the example outputs for the `analyse` command and the interactive mode (`-i`) to better reflect current functionality and showcase features.
    *   Added more badges for CI status, Python versions, and license.
    *   Restructured the feature sections and command-line reference for better readability.

## \[0.6.9] - 2025-07-19
### Fixed

*   **File Filtering**: The `--include` and `--exclude` flags now correctly handle recursive folder patterns, behaving like `.gitignore` (e.g., `--exclude "my_folder"` or `--exclude "my_folder/**"` will exclude all contents).

## \[0.6.8] - 2025-07-15

### Fixed

*   **Single File Input**: The CLI no longer errors when given a path to a single file (e.g., `ctp my_file.py`). It now correctly processes the specified file.
*   **Jupyter Notebook Processing**: Resolved an issue where processing `.ipynb` files could cause the tool to hang by including a necessary dependency (`ipython`).

## \[0.6.7] - 2025-07-12

### Added

*   **Jupyter Notebook Support**: Automatically processes `.ipynb` files by extracting Python code from all cells and including it in the prompt. This requires the `nbformat` and `nbconvert` packages.

### Fixed

*   **Tokenization Errors**: Fixed a critical bug where the tool would crash if a file's content included text that matched a special `tiktoken` token (e.g., `<|endoftext|>`). The tool now safely encodes such text.

## \[0.6.6] - 2025-07-11

### Added

*   **JavaScript Support in Web Scarping**: Added Javascript Support that will help to scrape JS Enabled Website.

## \[0.6.5] - 2025-07-07

### Added

*   **Remote URL Processing**: `codetoprompt` can now process content directly from the web, in addition to local directories.
    *   **GitHub Repositories**: Pass a GitHub URL to get a prompt of the entire codebase.
    *   **Web Pages**: Fetch and extract the main text from any website or documentation page.
    *   **YouTube Videos**: Automatically get the full transcript from a video URL.
    *   **ArXiv Papers & PDFs**: Extract text from ArXiv abstract pages or direct PDF links.

*   **Documentation**: Updated documentation.

## \[0.6.4] - 2025-07-05

### Updated

*   **Documentation**: Updated documentation.

## \[0.6.3] - 2025-07-03

### Updated

*   **Lazy Loading Implemented for Interactive Mode**: Implemented Lazy Loading for Interative Mode for Optimizing Interactive Mode on Huge Codebases.

## \[0.6.2] - 2025-07-01

### Updated

*   **Library Modularization**: Refactored CLI functionality into modular components for improved readability and maintainability.

## \[0.6.1] - 2025-06-21

### Added

*   **Interactive Mode**: Introduced a new `--interactive` (`-i`) flag that launches a file selection UI, allowing users to manually choose which files to include in the prompt. This provides fine-grained control over the context.

## \[0.6.0] - 2025-06-16

### Updated

*   **Documentation**: Improved and updated documentation.

## \[0.5.9] - 2025-06-16

### Fixed

*   **Code Compressor Bugs**: Resolved issues with unsupported languages in the compression process.

### Updated

*   **Dataset Detection**: Now reads the first 5 lines of dataset files to generate more effective prompts while reducing token usage.

## \[0.5.7] - 2025-06-16

### Updated

*   **Code Compressor**: Refactored into modular components.

### Added

*   **CLI Alias**: You can now invoke the CLI using `ctp` as a shorthand for `codetoprompt`.
*   **Version Flag**: Added `--version` and `-v` flags to display the current version (e.g., `codetoprompt --version` or `ctp -v`).

## \[0.5.5] - 2025-06-15

### Updated

*   **Documentation**: Added details for the compression feature and the `--markdown` (`-m`) and `--cxml` (`-c`) output modes.

## \[0.5.0] - 2025-06-15

### Added

*   **Code Compression**: Introduced a `--compress` flag that uses `tree-sitter` to parse supported code files (Python, JS, TS, Java, C/C++, Rust) into a structural summary. This significantly reduces the token count by omitting implementation details while preserving classes, functions, and signatures.
*   **Configurable Compression**: The `codetoprompt config` wizard now supports setting compression as a default.
*   **Fallback for Unsupported Files**: Files in unsupported languages (e.g., Markdown) are included in full.

## \[0.4.2] - 2025-06-15

### Added

*   **Flexible Output Formats**: Generate prompts in different formats using new CLI flags:
    *   `--markdown` (`-m`): Outputs file contents in fenced Markdown code blocks with language hints.
    *   `--cxml` (`-c`): Outputs file contents in a Claude-friendly XML structure.

### Changed

*   **Configuration Options**: The interactive wizard (`codetoprompt config`) and config file now support setting a default output format (`default`, `markdown`, or `cxml`).

## \[0.4.1] - 2025-06-14

### Added

*   **Codebase Analysis**: New `codetoprompt analyze` command for in-depth project statistics.
*   **Enhanced Prompt Summary**: Includes top files and file types by token count.

### Fixed

*   **Config Command Validation**: The `config` command now prevents invalid flag usage.
*   **UI Improvements**: Panels now correctly size to their content.

## \[0.4.0] - 2025-06-13

### Added

*   **Interactive Configuration Wizard**: Accessed via `codetoprompt config`.
*   **Config Management**: View and reset config with `codetoprompt config --show` and `codetoprompt config --reset`.
*   **Persistent Configuration File**: Stored at `~/.config/codetoprompt/config.toml`.

### Changed

*   **CLI Default Behavior**: Running `codetoprompt` with no arguments now shows the help menu.

## \[0.3.0] - 2025-06-12

### Added

*   **Project Structure Tree**: A visual tree of the project structure is now included in the prompt.

### Changed

*   **CLI Output Improvements**: Enhanced progress bar and more user feedback.

### Fixed

*   Multiple bugs related to tree generation, depth handling, and relative paths.
*   Clipboard and output file handling issues.

## \[0.2.0] - 2025-06-12

### Changed

*   **File Processing**: More robust handling of special tokens, problematic files, and file read errors.
*   **CLI Enhancements**: Added directory validation and improved argument parsing.

### Fixed

*   **Packaging & CI**: Corrected `pyproject.toml` and GitHub Actions workflows.
*   Multiple bugs in token counting and file handling logic.

## \[0.1.0] - 2025-06-11

### Added

*   Initial release.
*   Core functionality for converting a codebase into a single prompt.
*   File filtering, token counting, and a command-line interface.