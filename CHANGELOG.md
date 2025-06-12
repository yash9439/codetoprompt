# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.9] - 2024-03-12

### Fixed
- Fixed Tree Relative Path Bug

## [0.2.8] - 2024-03-12

### Fixed
- Fixed Pruned Tree Bug

## [0.2.7] - 2024-03-12

### Added
- Structure Tree Added

## [0.2.6] - 2024-03-12

### Changed
- CLI Visual Changes

## [0.2.5] - 2024-03-12

### Fixed
- Fixed prompt print issue
- Added confirmation msg upon successful run

## [0.2.4] - 2024-03-12

### Fixed
- Fixed process_files() function to properly handle copy_to_clipboard parameter
- Added clipboard functionality to process_files() function
- Added proper output handling for both file and stdout cases

## [0.2.3] - 2024-03-12

### Changed
- Added time elapsed column to progress bar
- Set copy to clipboard to True by default
- Improved progress bar visualization with bar column

## [0.2.0] - 2024-03-12

### Fixed
- Added proper directory validation in CLI
- Fixed error handling for non-existent directories
- Updated CLI tests to match new behavior

## [0.1.7] - 2024-03-12

### Fixed
- Fixed CLI argument handling in main function
- Ensured files are processed before token counting
- Removed clipboard functionality from tests
- Simplified test cases for better reliability

## [0.1.6] - 2024-03-12

### Fixed
- Fixed initialization of processed_files in CodeToPrompt class
- Simplified test cases for better reliability
- Improved error handling in file processing
- Fixed token counting for processed files

## [0.1.5] - 2025-06-12

### Fixed
- Fixed GitHub Actions workflow to properly install dev dependencies
- Updated actions/checkout to v4
- Fixed dependency installation command format

## [0.1.4] - 2025-06-12

### Fixed
- Fixed license configuration in pyproject.toml to comply with PEP 621
- Fixed pytest configuration and added pytest-cov dependency
- Fixed GitHub Actions workflow issues

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