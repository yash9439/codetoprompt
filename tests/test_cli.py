"""Tests for the CLI module."""

import os
from pathlib import Path

import pytest

from codetoprompt.cli import main


def test_cli_help(capsys):
    """Test CLI help message."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Convert code files to a prompt format" in captured.out


def test_cli_with_output(temp_dir, capsys):
    """Test CLI with output file."""
    # Create test file
    (temp_dir / "test.py").write_text("print('test')")

    # Run CLI with output file
    output_file = temp_dir / "output.txt"
    result = main([str(temp_dir), "--output", str(output_file)])
    assert result == 0
    assert output_file.exists()
    assert "print('test')" in output_file.read_text()


def test_cli_with_gitignore(temp_dir, capsys):
    """Test CLI with .gitignore."""
    # Create test files
    (temp_dir / "test.py").write_text("print('test')")
    (temp_dir / ".gitignore").write_text("*.py")
    (temp_dir / "test.txt").write_text("test")

    # Run CLI with gitignore
    result = main([str(temp_dir), "--respect-gitignore"])
    assert result == 0
    captured = capsys.readouterr()
    assert "print('test')" not in captured.out  # Should be ignored
    assert "test" in captured.out  # Should include non-Python files
