"""Tests for the CLI functionality of codetoprompt."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import toml

from codetoprompt.cli import main

# Fixture to provide a temporary, isolated config file for tests
@pytest.fixture
def mock_config_path(monkeypatch, tmp_path):
    """Mocks the config file path to use a temporary directory."""
    temp_config_dir = tmp_path / "config"
    temp_config_dir.mkdir()
    temp_config_file = temp_config_dir / "codetoprompt" / "config.toml"
    monkeypatch.setattr("codetoprompt.config.CONFIG_DIR", temp_config_dir / "codetoprompt")
    monkeypatch.setattr("codetoprompt.config.CONFIG_FILE", temp_config_file)
    return temp_config_file

# Re-use the project_dir fixture from test_core
@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary directory with a test project for CLI tests."""
    root = tmp_path / "test_project"
    root.mkdir()
    (root / "main.py").write_text("print('hello')")
    (root / "README.md").write_text("# Project")
    (root / ".gitignore").write_text("*.log\n")
    (root / "ignore.log").write_text("log message")
    sub_dir = root / "sub"
    sub_dir.mkdir()
    (sub_dir / "sub.py").write_text("print('sub')")
    return root

def test_cli_no_args(capsys):
    """Test that running with no arguments prints help and exits cleanly."""
    with patch("sys.argv", ["codetoprompt"]):
        return_code = main()
    
    captured = capsys.readouterr()
    assert return_code == 0
    assert "usage: codetoprompt" in captured.out
    assert "Generate a prompt" in captured.out

def test_cli_analyse(capsys, project_dir):
    """Test the analyse command from the CLI."""
    with patch("sys.argv", ["codetoprompt", "analyse", str(project_dir)]):
        return_code = main()
    
    captured = capsys.readouterr()
    assert return_code == 0
    assert "Codebase Analysis" in captured.out
    assert "Overall Project Summary" in captured.out
    assert "Analysis by File Type" in captured.out
    assert "Largest Files by Tokens" in captured.out

def test_cli_config_reset(capsys, mock_config_path):
    """Test 'config --reset' command."""
    mock_config_path.parent.mkdir(exist_ok=True, parents=True)
    mock_config_path.write_text("[settings]") # Ensure file exists
    assert mock_config_path.exists()

    with patch("sys.argv", ["codetoprompt", "config", "--reset"]):
        return_code = main()

    captured = capsys.readouterr()
    assert return_code == 0
    assert "Configuration has been reset" in captured.out
    assert not mock_config_path.exists()

def test_cli_config_invalid_flag(capsys):
    """Test that 'config' command handles invalid flags correctly."""
    with patch("sys.argv", ["codetoprompt", "config", "--invalid-flag"]):
        return_code = main()

    captured = capsys.readouterr()
    assert return_code == 1
    assert "Error: Unknown argument" in captured.out
    assert "--invalid-flag" in captured.out

def test_cli_config_show(capsys, mock_config_path):
    """Test the 'config --show' command."""
    with patch("sys.argv", ["codetoprompt", "config", "--show"]):
        return_code = main()
    
    captured = capsys.readouterr()
    assert return_code == 0
    assert "Current CodeToPrompt Defaults" in captured.out
    assert "Respect .gitignore" in captured.out
    assert "True" in captured.out

def test_cli_output_file_flag(project_dir, tmp_path):
    """Test the --output flag for saving to a file."""
    output_file = tmp_path / "output.txt"
    with patch("sys.argv", ["codetoprompt", str(project_dir), "--output", str(output_file)]):
        main()
    
    assert output_file.exists()
    content = output_file.read_text()
    assert "Project Structure" in content
    assert "main.py" in content

def test_cli_analyse_flags(capsys, project_dir):
    """Test flags for the 'analyse' command, like --top-n."""
    with patch("sys.argv", ["codetoprompt", "analyse", str(project_dir), "--top-n", "1"]):
        main()
    
    captured = capsys.readouterr()
    output_lines = captured.out.splitlines()
    # Count how many file rows are in the tables
    token_table_rows = [line for line in output_lines if "main.py" in line or "README.md" in line]
    assert len(token_table_rows) == 1

@pytest.mark.parametrize("path_arg", [
    "/path/that/does/not/exist",
    "pyproject.toml" # a file, not a directory
])
def test_cli_invalid_path_errors(capsys, path_arg):
    """Test that the CLI handles invalid paths gracefully."""
    with patch("sys.argv", ["codetoprompt", path_arg]):
        return_code = main()
    
    captured = capsys.readouterr()
    assert return_code == 1
    assert "Error:" in captured.out
    if "not/exist" in path_arg:
        assert "does not exist" in captured.out
    else:
        assert "is not a directory" in captured.out