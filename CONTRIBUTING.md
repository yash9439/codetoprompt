# Contributing to CodeToPrompt

Thank you for your interest in contributing to CodeToPrompt! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/codetoprompt.git
   cd codetoprompt
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure they pass all checks:
   ```bash
   # Format code
   black .
   isort .

   # Run type checking
   mypy .

   # Run linting
   flake8

   # Run tests
   pytest
   ```

3. Commit your changes with a descriptive message:
   ```bash
   git commit -m "feat: add new feature"
   ```

4. Push your branch and create a pull request

## Code Style

- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [mypy](https://mypy.readthedocs.io/) for type checking
- Use [flake8](https://flake8.pycqa.org/) for linting

## Testing

- Write tests for new features
- Ensure all tests pass before submitting a PR
- Maintain or improve test coverage

## Documentation

- Add docstrings to all public functions and classes
- Update README.md if needed
- Update CHANGELOG.md for significant changes

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with your changes
3. The PR will be merged once you have the sign-off of at least one maintainer 