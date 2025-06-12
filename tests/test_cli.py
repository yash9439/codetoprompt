"""Tests for the CLI functionality of codetoprompt."""
import os
import tempfile
from pathlib import Path

import pytest
from codetoprompt.cli import main

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

def test_cli_basic_usage(temp_dir, capsys):
    """Test basic CLI usage."""
    # Mock sys.argv
    import sys
    sys.argv = ["codetoprompt", str(temp_dir)]
    
    # Run CLI
    result = main()
    assert result == 0
    
    # Check output
    captured = capsys.readouterr()
    assert "Configuration" in captured.out
    assert "Processing Complete" in captured.out
    assert "Total Tokens" in captured.out

def test_cli_with_output(temp_dir, capsys):
    """Test CLI with output file."""
    output_file = temp_dir / "output.txt"
    
    # Mock sys.argv
    import sys
    sys.argv = ["codetoprompt", str(temp_dir), "--output", str(output_file)]
    
    # Run CLI
    result = main()
    assert result == 0
    
    # Check output file
    assert output_file.exists()
    content = output_file.read_text()
    assert "test1.py" in content
    assert "test2.py" in content
    assert "test4.py" in content
    assert "<|endoftext|>" in content

def test_cli_with_patterns(temp_dir, capsys):
    """Test CLI with include/exclude patterns."""
    # Mock sys.argv
    import sys
    sys.argv = [
        "codetoprompt",
        str(temp_dir),
        "--include", "*.py",
        "--exclude", "test2.py"
    ]
    
    # Run CLI
    result = main()
    assert result == 0
    
    # Check output
    captured = capsys.readouterr()
    output = captured.out
    # Only check the 'Generated Prompt' section
    if "Generated Prompt:" in output:
        prompt_section = output.split("Generated Prompt:", 1)[1]
    else:
        prompt_section = output
    assert "test1.py" in prompt_section
    assert "test2.py" not in prompt_section
    assert "test3.txt" not in prompt_section
    assert "test4.py" in prompt_section
    assert "<|endoftext|>" in prompt_section

def test_cli_invalid_directory(capsys):
    """Test CLI with invalid directory."""
    # Mock sys.argv
    import sys
    sys.argv = ["codetoprompt", "/nonexistent/directory"]
    
    # Run CLI
    result = main()
    assert result == 1
    
    # Check error message
    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "does not exist" in captured.out 