"""Tests for the CLI module."""

import pytest
from codetoprompt.cli import main

def test_cli_help(capsys):
    """Test CLI help message."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Convert code files to a prompt format" in captured.out
