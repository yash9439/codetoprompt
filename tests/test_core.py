"""Tests for the core functionality of codetoprompt."""
import os
import tempfile
from pathlib import Path

import pytest
from codetoprompt import CodeToPrompt

@pytest.fixture
def temp_dir():
    """Create a temporary directory with some test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        test_dir = Path(tmpdir)
        (test_dir / "test1.py").write_text("print('hello')\n")
        (test_dir / "test2.py").write_text("def test():\n    pass\n")
        (test_dir / "test3.txt").write_text("Some text\n")
        # Add a file with special tokens to test tokenizer
        (test_dir / "test4.py").write_text("<|endoftext|>\nprint('special token')\n")
        yield test_dir

def test_initialization(temp_dir):
    """Test CodeToPrompt initialization."""
    processor = CodeToPrompt(str(temp_dir))
    assert processor.root_dir == temp_dir
    assert processor.include_patterns == ["*"]
    assert processor.exclude_patterns == []
    assert processor.respect_gitignore is True
    assert processor.show_line_numbers is True

def test_file_inclusion(temp_dir):
    """Test file inclusion patterns."""
    processor = CodeToPrompt(
        str(temp_dir),
        include_patterns=["*.py"],
        exclude_patterns=["test2.py"]
    )
    files = list(processor._get_files())
    assert len(files) == 2  # test1.py and test4.py
    assert any(f.name == "test1.py" for f in files)
    assert any(f.name == "test4.py" for f in files)

def test_generate_prompt(temp_dir):
    """Test prompt generation."""
    processor = CodeToPrompt(str(temp_dir))
    prompt = processor.generate_prompt()
    assert "test1.py" in prompt
    assert "test2.py" in prompt
    assert "test3.txt" in prompt
    assert "test4.py" in prompt
    assert "print('hello')" in prompt
    assert "<|endoftext|>" in prompt

def test_token_count(temp_dir):
    """Test token counting."""
    processor = CodeToPrompt(str(temp_dir))
    count = processor.get_token_count()
    assert count > 0
    # Test with special tokens
    processor = CodeToPrompt(str(temp_dir), include_patterns=["test4.py"])
    count = processor.get_token_count()
    assert count > 0

def test_save_to_file(temp_dir):
    """Test saving prompt to file."""
    processor = CodeToPrompt(str(temp_dir))
    output_file = temp_dir / "output.txt"
    processor.save_to_file(str(output_file))
    assert output_file.exists()
    content = output_file.read_text()
    assert "test1.py" in content
    assert "test2.py" in content
    assert "test4.py" in content
    assert "<|endoftext|>" in content 