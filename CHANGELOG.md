# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.5.7] - 2025-06-16

### Update
 **Code Compressor**: Modularization
 
### Added
 **CLI Alias**: The CLI can now be invoked with `ctp` as a shorter alias for `codetoprompt`.
 **Version Flag**: Added a `--version` (and `-v`) flag to display the current version number (e.g., `codetoprompt --version` or `ctp -v`).


## [0.5.5] - 2025-06-15

### Update
- **Documentation Update**: Updated Documentation for the Compression Feature and the -c, -m modes for prompt generation.

## [0.5.0] - 2025-06-15

### Added
- **Code Compression**: A new `--compress` flag uses `tree-sitter` to parse supported code files (Python, JS, TS, Java, C/C++, Rust) into a structural summary. This dramatically reduces token count by omitting implementation details while preserving classes, functions, and signatures.
- **Compression in Configuration**: The `codetoprompt config` wizard now allows setting compression as a default.
- Files that cannot be compressed (e.g., unsupported languages, markdown) are included in their entirety as a fallback.


## [0.4.2] - 2025-06-15

### Added
- **Flexible Output Formats**: Generate prompts in different formats using new CLI flags.
  - `--markdown` (`-m`): Outputs file content in fenced Markdown code blocks with language hints.
  - `--cxml` (`-c`): Outputs file content in a Claude-friendly XML structure.

### Changed
- **Configuration Update**: The interactive wizard (`codetoprompt config`) and config file now support setting a default output format (`default`, `markdown`, or `cxml`).

## [0.4.1] - 2025-06-14

### Added
- **Codebase Analysis Command**: `codetoprompt analyse` for in-depth project statistics.
- **Enhanced Prompt Summary**: Now includes top files and file types by token count.

### Fixed
- **Strict `config` Command**: Prevents running the wizard with invalid flags.
- **Improved UI Consistency**: Panels now correctly size to their content.

## [0.4.0] - 2025-06-13

### Added
- Interactive configuration wizard via `codetoprompt config`.
- View/Reset configuration with `config --show` and `config --reset`.
- Persistent configuration file at `~/.config/codetoprompt/config.toml`.

### Changed
- Bare `codetoprompt` command now shows help instead of running.

## [0.3.0] - 2025-06-12

### Added
- **Project Structure Tree**: Adds a visual tree of the project structure to the prompt.

### Changed
- **Improved CLI Output**: Enhanced progress bar and added more user feedback.

### Fixed
- Multiple bugs related to tree generation, including depth and relative paths.
- Improved clipboard and output file handling.

## [0.2.0] - 2025-06-12

### Changed
- **Robust File Processing**: Improved handling of special tokens, problematic files, and errors.
- **Improved CLI**: Added directory validation and better argument handling.

### Fixed
- **Packaging & CI**: Corrected `pyproject.toml` and GitHub Actions workflow issues.
- Multiple bugs in token counting and file processing logic.

## [0.1.0] - 2025-06-11

### Added
- Initial release.
- Core functionality for converting a codebase to a single prompt.
- File filtering, token counting, and a command-line interface.