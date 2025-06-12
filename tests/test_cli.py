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
    main([str(temp_dir), "--include", "*.py", "--exclude", "test2.py"])
    captured = capsys.readouterr()
    assert "test1.py" in captured.out
    assert "test2.py" not in captured.out


def test_cli_invalid_directory(capsys):
    """Test CLI with invalid directory."""
    result = main(["/nonexistent/directory"])
    captured = capsys.readouterr()
    assert result == 1
    assert "Error: Directory '/nonexistent/directory' does not exist" in captured.out
