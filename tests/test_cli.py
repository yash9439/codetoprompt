"""Tests for the CLI functionality of codetoprompt."""

import os
import tempfile
from pathlib import Path

import pytest
from codetoprompt.cli import main


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create test files
    test1 = tmp_path / "test1.py"
    test1.write_text("print('Hello, World!')")

    test2 = tmp_path / "test2.py"
    test2.write_text("def test():\n    pass")

    return tmp_path


def test_cli_basic_usage(temp_dir, capsys):
    """Test basic CLI usage."""
    main([str(temp_dir)])
    captured = capsys.readouterr()
    assert "test1.py" in captured.out
    assert "test2.py" in captured.out
    assert "print('Hello, World!')" in captured.out


def test_cli_with_output(temp_dir):
    """Test CLI with output file."""
    output_file = temp_dir / "output.txt"
    main([str(temp_dir), "--output", str(output_file)])

    assert output_file.exists()
    content = output_file.read_text()
    assert "test1.py" in content
    assert "test2.py" in content


def test_cli_with_patterns(temp_dir, capsys):
    """Test CLI with file patterns."""
    # Create test files
    (temp_dir / "test1.py").write_text("print('test1')")
    (temp_dir / "test2.py").write_text("print('test2')")
    (temp_dir / "test3.txt").write_text("test3")

    # Run CLI with show line numbers
    result = main([str(temp_dir), "--show-line-numbers"])
    assert result == 0
    captured = capsys.readouterr()
    assert "1: print('test1')" in captured.out
    assert "1: print('test2')" in captured.out
    assert "test3" not in captured.out  # Should not include non-Python files


def test_cli_invalid_directory(capsys):
    """Test CLI with invalid directory."""
    result = main(["/nonexistent/directory"])
    assert result == 1
    captured = capsys.readouterr()
    assert "Error: Directory '/nonexistent/directory' does not exist" in captured.err


def test_cli_help(capsys):
    """Test CLI help message."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Convert code files to a prompt format" in captured.out


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
