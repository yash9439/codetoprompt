# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-06-12

### Changed
- Made token counting more robust by skipping problematic files instead of failing
- Improved error handling in prompt generation to continue processing even if some files fail
- Added warning messages for skipped files and token counting issues

## [0.1.2] - 2025-06-12

### Fixed
- Fixed special token handling in tiktoken by properly configuring both `allowed_special` and `disallowed_special`
- Ensures all special tokens are processed as normal text without errors

## [0.1.1] - 2025-06-12

### Fixed
- Fixed special token handling in tiktoken
- Fixed truncated lines in core.py
- Fixed test cases for special token handling

### Changed
- Improved error handling
- Enhanced tokenizer configuration
- Improved test coverage
- Better CLI output formatting

## [0.1.0] - 2025-06-11

### Added
- Initial release
- Basic codebase to prompt conversion
- File pattern filtering
- Token counting
- CLI interface

### Fixed
- Fixed special token handling in tiktoken to prevent errors with `<|endoftext|>` and similar tokens
- Fixed truncated lines in core functionality
- Fixed test cases to properly handle special tokens
- Improved error handling and warning messages

### Changed
- Updated tokenizer configuration to handle all text content without restrictions
- Enhanced test coverage for special token cases
- Improved CLI output formatting 