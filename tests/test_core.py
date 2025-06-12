"""Tests for the core functionality of codetoprompt."""

import os
import tempfile
from pathlib import Path

import pytest
from codetoprompt.core import CodeToPrompt


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create test files
    test1 = tmp_path / "test1.py"
    test1.write_text("print('Hello, World!')")

    test2 = tmp_path / "test2.py"
    test2.write_text("def test():\n    pass")

    return tmp_path


def test_initialization(temp_dir):
    """Test basic initialization."""
    processor = CodeToPrompt(str(temp_dir))
    assert processor.root_dir == temp_dir
    assert processor.include_patterns == ["*"]
    assert processor.exclude_patterns == []
    assert processor.show_line_numbers is True


def test_file_processing(temp_dir):
    """Test file processing."""
    processor = CodeToPrompt(str(temp_dir))
    prompt = processor.generate_prompt()

    # Check if both test files are included
    assert "test1.py" in prompt
    assert "test2.py" in prompt
    assert "print('Hello, World!')" in prompt
    assert "def test():" in prompt


def test_token_count(temp_dir):
    """Test token counting."""
    processor = CodeToPrompt(str(temp_dir))
    # Generate prompt first to ensure files are processed
    processor.generate_prompt()
    count = processor.get_token_count()
    assert count > 0  # Should have some tokens


def test_save_to_file(temp_dir):
    """Test saving prompt to file."""
    processor = CodeToPrompt(str(temp_dir))
    output_file = temp_dir / "output.txt"
    processor.save_to_file(str(output_file))

    # Check if file was created and contains content
    assert output_file.exists()
    content = output_file.read_text()
    assert "test1.py" in content
    assert "test2.py" in content
