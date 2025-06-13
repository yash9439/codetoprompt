"""Tests for the CLI functionality of codetoprompt."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from codetoprompt.cli import main

# Fixture to provide a temporary, isolated config file for tests
@pytest.fixture
def mock_config_path(monkeypatch, tmp_path):
    """Mocks the config file path to use a temporary directory."""
    temp_config_file = tmp_path / "config.toml"
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
    return root

def test_cli_no_args(capsys):
    """Test that running with no arguments prints help and exits cleanly."""
    # Mock sys.argv
    with patch("sys.argv", ["codetoprompt"]):
        return_code = main()
    
    captured = capsys.readouterr()
    assert return_code == 0
    assert "usage: codetoprompt" in captured.out
    assert "Generate a prompt" in captured.out

@patch("pyperclip.copy", MagicMock())
def test_cli_prompt_generation(capsys, project_dir):
    """Test a basic prompt generation run from the CLI."""
    with patch("sys.argv", ["codetoprompt", str(project_dir)]):
        return_code = main()

    captured = capsys.readouterr()
    assert return_code == 0
    assert "Processing Complete" in captured.out
    assert "main.py" in captured.out
    assert "README.md" in captured.out
    # Test that .gitignore was respected
    assert "ignore.log" not in captured.out
    assert "Top 3 Files by Tokens" in captured.out

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