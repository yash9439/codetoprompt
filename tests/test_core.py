"""Tests for the core functionality of codetoprompt."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
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
    # Add a file with backticks to test markdown escaping
    (root / "script.js").write_text("console.log(`hello ``` world`);")

    data_dir = root / "data"
    data_dir.mkdir()
    (data_dir / "config.json").write_text('{"key": "value"}')
    (data_dir / "users.csv").write_text('id,name\n1,test')
    (data_dir / "binary.dat").write_text(b'\x00\x01\x02\x03'.decode('latin-1'))  # Simulate binary

    tests_dir = root / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main():\n    assert True")
    sub_tests_dir = tests_dir / "sub"
    sub_tests_dir.mkdir()
    (sub_tests_dir / "sub_test.py").write_text("def test_sub(): pass")

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
    assert processor.include_patterns == ["**"]
    assert processor.exclude_patterns == []
    assert processor.show_line_numbers is False
    # Test new default
    assert processor.output_format == "default"

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
    assert "script.js" in processed_paths
    
    # Should be excluded by .gitignore
    assert "data/users.csv" not in processed_paths
    assert ".env" not in processed_paths
    assert ".cache/cachefile" not in processed_paths

def test_output_formats(project_dir):
    """Test that prompt generation works correctly for all output formats."""
    # 1. Test "default" format
    processor_default = CodeToPrompt(str(project_dir), include_patterns=["main.py"])
    prompt_default = processor_default.generate_prompt()
    assert "Relative File Path: main.py" in prompt_default
    assert "```" in prompt_default
    assert "print('main')" in prompt_default

    # 2. Test "markdown" format
    processor_md = CodeToPrompt(str(project_dir), output_format="markdown", include_patterns=["main.py", "script.js"])
    prompt_md = processor_md.generate_prompt()
    assert "main.py" in prompt_md
    assert "script.js" in prompt_md
    assert "```python" in prompt_md
    assert "````javascript" in prompt_md # Test backtick escaping
    assert "console.log(`hello ``` world`);" in prompt_md
    assert "Relative File Path:" not in prompt_md

    # 3. Test "cxml" format
    processor_cxml = CodeToPrompt(str(project_dir), output_format="cxml", include_patterns=["main.py"])
    prompt_cxml = processor_cxml.generate_prompt()
    assert "<documents>" in prompt_cxml
    assert '</documents>' in prompt_cxml
    assert '<document index="1">' in prompt_cxml
    assert "<source>main.py</source>" in prompt_cxml
    assert "<document_content>" in prompt_cxml
    assert "print('main')" in prompt_cxml

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
    analysis = processor.analyse()

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

def test_save_to_file(project_dir, tmp_path):
    """Test saving the generated prompt to a file."""
    output_file = tmp_path / "prompt.txt"
    processor = CodeToPrompt(str(project_dir), include_patterns=["README.md"])
    processor.save_to_file(str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text()
    assert "Project Structure" in content
    assert "# Test Project" in content

def test_max_tokens_warning(project_dir, capsys):
    """Test that a warning is printed if the token count exceeds max_tokens."""
    processor = CodeToPrompt(str(project_dir), max_tokens=10)
    processor.generate_prompt()
    captured = capsys.readouterr()
    assert "Warning: Prompt exceeds token limit" in captured.out

def test_data_file_small_included_in_full(tmp_path):
    """Small data files (under threshold) are included verbatim, not truncated."""
    root = tmp_path / "p"
    root.mkdir()
    # 12-line JSON — well under the default threshold of 50
    small = "\n".join(f'{{"i": {i}}}' for i in range(12))
    (root / "tiny.json").write_text(small)

    processor = CodeToPrompt(str(root), respect_gitignore=False)
    prompt = processor.generate_prompt()

    assert '{"i": 11}' in prompt
    assert "Data file content truncated" not in prompt


def test_data_file_large_truncated_when_enabled(tmp_path):
    """Large data files exceeding the threshold are cut to DATA_FILE_LINE_LIMIT."""
    root = tmp_path / "p"
    root.mkdir()
    big = "\n".join(f'{{"i": {i}}}' for i in range(200))
    (root / "big.json").write_text(big)

    processor = CodeToPrompt(
        str(root),
        respect_gitignore=False,
        data_file_threshold_lines=50,
    )
    prompt = processor.generate_prompt()

    assert '{"i": 0}' in prompt
    assert '{"i": 199}' not in prompt
    assert "Data file content truncated" in prompt


def test_data_file_truncation_toggle_off(tmp_path):
    """With truncate_data_files=False, even huge data files are kept in full."""
    root = tmp_path / "p"
    root.mkdir()
    big = "\n".join(f'{{"i": {i}}}' for i in range(200))
    (root / "big.json").write_text(big)

    processor = CodeToPrompt(
        str(root),
        respect_gitignore=False,
        truncate_data_files=False,
    )
    prompt = processor.generate_prompt()

    assert '{"i": 199}' in prompt
    assert "Data file content truncated" not in prompt


def test_data_file_sibling_clustering(tmp_path):
    """Many same-extension data files in one dir are sampled, the rest summarised."""
    root = tmp_path / "p"
    root.mkdir()
    ds = root / "dataset"
    ds.mkdir()
    for i in range(20):
        (ds / f"record_{i:02d}.json").write_text(f'{{"i": {i}}}')

    processor = CodeToPrompt(
        str(root),
        respect_gitignore=False,
        data_file_max_per_dir=5,
    )
    prompt = processor.generate_prompt()

    processed_names = {p.name for p in processor.processed_files.keys()}
    json_kept = [n for n in processed_names if n.startswith("record_")]
    assert len(json_kept) == 5
    # Lexicographically first 5 should be kept
    assert "record_00.json" in json_kept
    assert "record_04.json" in json_kept
    assert "record_05.json" not in json_kept
    # Summary section is appended
    assert "Omitted Data File Groups" in prompt
    assert "kept 5 of 20" in prompt
    assert "omitted 15" in prompt


def test_data_file_sibling_clustering_disabled(tmp_path):
    """data_file_max_per_dir=0 disables clustering — all files pass through."""
    root = tmp_path / "p"
    root.mkdir()
    ds = root / "dataset"
    ds.mkdir()
    for i in range(10):
        (ds / f"record_{i}.json").write_text(f'{{"i": {i}}}')

    processor = CodeToPrompt(
        str(root),
        respect_gitignore=False,
        data_file_max_per_dir=0,
    )
    processor.generate_prompt()

    processed_names = {p.name for p in processor.processed_files.keys()}
    json_kept = [n for n in processed_names if n.startswith("record_")]
    assert len(json_kept) == 10
    assert processor.omitted_data_groups == []


def test_cxml_escapes_closing_tag_in_content(tmp_path):
    """File content containing </document_content> must not break CXML output."""
    root = tmp_path / "p"
    root.mkdir()
    (root / "evil.md").write_text("before </document_content> after")

    processor = CodeToPrompt(
        str(root),
        respect_gitignore=False,
        output_format="cxml",
        include_patterns=["evil.md"],
    )
    prompt = processor.generate_prompt()

    # Exactly one real closing tag per document — the one in content is neutralized.
    assert prompt.count("</document_content>") == 1
    assert "before" in prompt and "after" in prompt


def test_empty_directory_prompt(tmp_path):
    """Test prompt generation for an empty directory."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    processor = CodeToPrompt(str(empty_dir))
    prompt = processor.generate_prompt()
    assert "No files found matching the specified criteria." in prompt