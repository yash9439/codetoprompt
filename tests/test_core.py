"""Tests for the core functionality of codetoprompt."""

import pytest
from pathlib import Path
from codetoprompt.core import CodeToPrompt

# A more complex project structure for thorough testing
@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary directory with a complex project structure for testing."""
    root = tmp_path / "test_project"
    root.mkdir()

    # Create files with varied content and extensions
    (root / "main.py").write_text("import utils\n\nprint('main')\n" * 10)  # 30 lines
    (root / "utils.py").write_text("def helper():\n    pass\n" * 5)  # 10 lines
    (root / "README.md").write_text("# Test Project\n" * 3)  # 3 lines

    data_dir = root / "data"
    data_dir.mkdir()
    (data_dir / "config.json").write_text('{"key": "value"}')
    (data_dir / "users.csv").write_text('id,name\n1,test')
    (data_dir / "binary.dat").write_text(b'\x00\x01\x02\x03'.decode('latin-1'))  # Simulate binary

    tests_dir = root / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main():\n    assert True")

    # Hidden files and folders
    (root / ".env").write_text("SECRET=KEY")
    (root / ".cache").mkdir()
    (root / ".cache" / "cachefile").write_text("cached")

    # Gitignore file
    (root / ".gitignore").write_text("*.csv\n.env\n.cache/\n")

    return root

def test_initialization(project_dir):
    """Test that the CodeToPrompt class initializes correctly."""
    processor = CodeToPrompt(str(project_dir))
    assert processor.root_dir == project_dir.resolve()
    assert processor.include_patterns == ["*"]
    assert processor.exclude_patterns == []
    assert processor.show_line_numbers is True

def test_file_processing_default(project_dir):
    """Test default file processing (respect .gitignore, include all)."""
    processor = CodeToPrompt(str(project_dir), respect_gitignore=True)
    processor.generate_prompt()
    
    processed_paths = {str(p.relative_to(project_dir)) for p in processor.processed_files.keys()}
    
    # Should be included
    assert "main.py" in processed_paths
    assert "README.md" in processed_paths
    assert "tests/test_main.py" in processed_paths
    assert "data/config.json" in processed_paths
    
    # Should be excluded by .gitignore
    assert "data/users.csv" not in processed_paths
    assert ".env" not in processed_paths
    assert ".cache/cachefile" not in processed_paths

def test_filtering_include(project_dir):
    """Test include glob patterns."""
    processor = CodeToPrompt(str(project_dir), include_patterns=["*.md"], respect_gitignore=False)
    processor.generate_prompt()
    processed_paths = {str(p.relative_to(project_dir)) for p in processor.processed_files.keys()}
    
    assert processed_paths == {"README.md"}

def test_filtering_exclude(project_dir):
    """Test exclude glob patterns."""
    processor = CodeToPrompt(str(project_dir), exclude_patterns=["tests/*"], respect_gitignore=False)
    processor.generate_prompt()
    processed_paths = {str(p.relative_to(project_dir)) for p in processor.processed_files.keys()}

    assert "tests/test_main.py" not in processed_paths
    assert "main.py" in processed_paths

def test_no_respect_gitignore(project_dir):
    """Test that gitignore rules are ignored when specified."""
    processor = CodeToPrompt(str(project_dir), respect_gitignore=False)
    processor.generate_prompt()
    processed_paths = {str(p.relative_to(project_dir)) for p in processor.processed_files.keys()}

    # All text files should now be included
    assert "data/users.csv" in processed_paths
    assert ".env" in processed_paths
    # .cache is still skipped due to being a hidden directory
    assert ".cache/cachefile" not in processed_paths

def test_token_and_line_counts(project_dir):
    """Test that token and line counts are calculated correctly."""
    processor = CodeToPrompt(str(project_dir), respect_gitignore=False, include_patterns=["main.py"])
    analysis = processor.analyze()

    assert analysis["overall"]["file_count"] == 1
    # main.py has 30 lines
    assert analysis["overall"]["total_lines"] == 30
    # Check that token count is reasonable
    assert analysis["overall"]["total_tokens"] > 30

def test_binary_file_skipping(project_dir):
    """Ensure that binary files are skipped."""
    # Add a known binary extension file
    (project_dir / "image.png").write_text("not really a png")
    
    processor = CodeToPrompt(str(project_dir))
    processor.generate_prompt()
    processed_paths = {p.name for p in processor.processed_files.keys()}
    
    assert "binary.dat" not in processed_paths
    assert "image.png" not in processed_paths